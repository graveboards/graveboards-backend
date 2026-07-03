import asyncio
import secrets
from contextlib import contextmanager, asynccontextmanager
from typing import AsyncIterator, Generator, Any

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.config import REDIS_CONFIGURATION
from app.exceptions import RedisLockTimeoutError
from app.logging import get_logger
from .constants import LOCK_EXPIRY, LOCK_ACQUISITION_RETRY_INTERVAL, LOCK_ACQUISITION_TIMEOUT

__all__ = [
    "RedisClient",
    "redis_connection"
]

REDIS_BASE_URL = f"redis://{REDIS_CONFIGURATION["username"]}:***@{REDIS_CONFIGURATION["host"]}:{REDIS_CONFIGURATION["port"]}/{REDIS_CONFIGURATION["db"]}"
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

    async def paginate_scan(
        self,
        pattern: str,
        limit: int = None,
        offset: int = 0,
        type_: str = None
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
        retry_interval: float = LOCK_ACQUISITION_RETRY_INTERVAL
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
            ``None``.

        Raises:
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
def redis_connection() -> Generator[Redis, Any, None]:
    """Provide a synchronous Redis connection from the shared pool.

    Yields:
        Redis: A Redis client instance.
    """
    from .pool import connection_pool

    rc = Redis(connection_pool=connection_pool)

    try:
        yield rc
    finally:
        rc.close()
