"""Async Redis client with command instrumentation and distributed locking."""

from __future__ import annotations

import asyncio
import secrets
import time
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Any, Literal

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.config import REDIS_CONFIGURATION
from app.exceptions import RedisLockTimeoutError
from app.observability.logging import get_logger
from app.observability.metrics.redis import (
    redis_cache_hits_total,
    redis_cache_misses_total,
    redis_commands_duration_seconds,
    redis_commands_total,
)

from .constants import LOCK_ACQUISITION_RETRY_INTERVAL, LOCK_ACQUISITION_TIMEOUT, LOCK_EXPIRY

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Generator, Mapping, Sequence

    from redis.typing import EncodableT, FieldT, KeyT

__all__ = ["RedisClient", "redis_connection"]

REDIS_BASE_URL = f"redis://{REDIS_CONFIGURATION['username']}:***@{REDIS_CONFIGURATION['host']}:{REDIS_CONFIGURATION['port']}/{REDIS_CONFIGURATION['db']}"
logger = get_logger(__name__)


class RedisClient(AsyncRedis):
    """Asynchronous Redis client interface.

    Designed to centralize redis concerns behind a thin, composable abstraction.
    Uses connection pooling to efficiently reuse connections.
    """

    def __init__(self) -> None:
        """Initialize the Redis client using configured connection settings."""
        super().__init__(**REDIS_CONFIGURATION)
        logger.debug(f"Redis client initialized at '{REDIS_BASE_URL}'")

    async def execute_command(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a Redis command with Prometheus metrics instrumentation.

        Args:
            *args:
                Command arguments.
            **kwargs:
                Command keyword arguments.

        Returns:
            The command result.
        """
        command_name = args[0].upper() if args else "UNKNOWN"
        start = time.perf_counter()

        try:
            result = await super().execute_command(*args, **kwargs)  # type: ignore[no-untyped-call]
            redis_commands_total.labels(command=command_name, status="success").inc()

            if command_name == "GET" and result is not None:
                redis_cache_hits_total.inc()
            elif command_name == "GET" and result is None:
                redis_cache_misses_total.inc()

            return result
        except Exception:
            redis_commands_total.labels(command=command_name, status="error").inc()
            raise
        finally:
            duration = time.perf_counter() - start
            redis_commands_duration_seconds.labels(command=command_name).observe(duration)

    # redis-py types async commands as `Awaitable[T] | T` (shared stubs with the
    # sync client). Since RedisClient is async-only, redeclare the commands used
    # across the codebase with their resolved (awaited) return types so callers can
    # `await` them directly. Parameter types mirror the base class exactly so the
    # overrides stay Liskov-compatible.
    async def hgetall(self, name: KeyT) -> dict[str | bytes, str | bytes]:
        """Return the whole hash stored at ``name`` (awaited, typed)."""
        return await super().hgetall(name)

    async def hset(
        self,
        name: KeyT,
        key: FieldT | None = None,
        value: EncodableT | None = None,
        mapping: Mapping[Any, Any] | None = None,
        items: Sequence[EncodableT] | None = None,
    ) -> int:
        """Set one or more fields in the hash at ``name``; returns the field count."""
        return await super().hset(name, key=key, value=value, mapping=mapping, items=items)

    async def sismember(self, name: KeyT, value: str) -> Literal[0, 1]:
        """Return whether ``value`` is a member of the set at ``name``."""
        return await super().sismember(name, value)

    async def sadd(self, name: KeyT, *values: FieldT) -> int:
        """Add members to the set at ``name``; returns the number added."""
        return await super().sadd(name, *values)

    async def smembers(self, name: KeyT) -> set[str | bytes]:
        """Return all members of the set at ``name``."""
        return await super().smembers(name)

    async def eval(self, script: str, numkeys: int, *keys_and_args: KeyT | EncodableT) -> Any:
        """Evaluate a Lua script server-side."""
        return await super().eval(script, numkeys, *keys_and_args)

    async def ping(self, **kwargs: Any) -> bool:
        """Ping the Redis server; returns True when reachable."""
        return await super().ping(**kwargs)

    async def paginate_scan(
        self, pattern: str, limit: int | None = None, offset: int = 0, type_: str | None = None
    ) -> list[str]:
        """Scan keys matching a pattern with offset/limit pagination.

        Uses Redis SCAN with a batch count to minimize round trips. Offset filtering
        is performed in Python since Redis SCAN does not support server-side offset.

        Args:
            pattern:
                Glob-style key pattern.
            limit:
                Maximum number of keys to return.
            offset:
                Number of matching keys to skip.
            type_:
                Optional Redis type filter.

        Returns:
        -------
            A list of matching Redis keys.
        """
        keys = []
        scanned = 0
        scan_count = max(limit or 100, 100)

        async for key in self.scan_iter(match=pattern, _type=type_, count=scan_count):
            if scanned < offset:
                scanned += 1
                continue

            keys.append(key)

            if limit is not None and len(keys) >= limit:
                break

        return keys

    @asynccontextmanager
    async def lock_ctx(
        self,
        key: str,
        expiry: int = LOCK_EXPIRY,
        timeout: float = LOCK_ACQUISITION_TIMEOUT,
        retry_interval: float = LOCK_ACQUISITION_RETRY_INTERVAL,
    ) -> AsyncIterator[None]:
        """Acquire a distributed lock using Redis SET NX semantics.

        Retries until acquired or timeout is reached. Automatically releases the lock on
        context exit, but only if it still owns the lock.

        Args:
            key:
                Lock key.
            expiry:
                Lock expiration time in seconds.
            timeout:
                Maximum time to wait for acquisition.
            retry_interval:
                Delay between retry attempts.

        Yields:
        ------
            ``None``.

        Raises:
        ------
            RedisLockTimeoutError:
                If the lock cannot be acquired in time.
        """
        token = secrets.token_urlsafe()
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            if await self.set(key, token, ex=expiry, nx=True):
                break

            if loop.time() > deadline:
                raise RedisLockTimeoutError(key, timeout)

            await asyncio.sleep(retry_interval)

        try:
            yield
        finally:
            lua = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.eval(lua, 1, key, token)


@contextmanager
def redis_connection() -> Generator[Redis, Any]:
    """Provide a synchronous Redis connection from the shared pool.

    Yields:
    ------
        Redis: A Redis client instance.
    """
    from .pool import connection_pool

    rc = Redis(connection_pool=connection_pool)

    try:
        yield rc
    finally:
        rc.close()
