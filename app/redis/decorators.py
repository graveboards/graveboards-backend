import asyncio
import inspect
from typing import Callable, Awaitable, ParamSpec, TypeVar, runtime_checkable, Protocol
from functools import wraps
from datetime import timedelta

from app.exceptions import RateLimitExceededError
from app.logging import get_logger
from app.utils import aware_utcnow
from .rc import RedisClient
from .enums import Namespace

__all__ = [
    "rate_limit"
]

P = ParamSpec("P")
T = TypeVar("T")
logger = get_logger(__name__)


@runtime_checkable
class _HasRedisClient(Protocol):
    """Protocol for objects exposing a Redis client via `rc`."""

    rc: object


@runtime_checkable
class _HasIncrExpire(Protocol):
    """Protocol for Redis-like objects with async incr and expire methods."""

    async def incr(self, name: str) -> int: ...
    async def expire(self, name: str, time: int) -> bool: ...


def rate_limit(
    limit_per_window: int | None = None,
    window_size: int = 60,
    min_interval: float = 0.0,
    auto_retry: bool = True,
    retry_backoff: float = 1.0,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for Redis-backed per-minute rate limiting with min-interval gating.

    Enforces two independent constraints:
    - min_interval: Hard minimum seconds between individual calls (always enforced).
    - limit_per_window: Maximum calls per ``window_size``-second rolling window.

    Both checks apply independently. A call must pass both to proceed.

    Args:
        limit_per_window:
            Maximum allowed executions per window. ``None`` disables window-based
            limiting. Defaults to ``60`` when omitted.
        window_size:
            Window size in seconds. Defaults to ``60``.
        min_interval:
            Minimum seconds between individual calls. Defaults to ``0.0``
            (disabled). When ``> 0``, sleeps the difference if the previous call
            was too recent.
        auto_retry:
            Whether to wait and retry automatically when the window limit is
            exceeded. Defaults to ``True``.
        retry_backoff:
            Base backoff in seconds for retry sleep. Defaults to ``1.0``.

    Raises:
        ValueError:
            If applied to a non-async function.
    """
    if limit_per_window is None:
        limit_per_window = 60

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @rate_limit")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            obj = args[0] if args else None
            rc: RedisClient | object | None = None

            if isinstance(obj, RedisClient):
                rc = obj
            elif obj is not None and hasattr(obj, 'rc'):
                rc = obj.rc
            elif obj is not None and hasattr(obj, 'incr') and hasattr(obj, 'expire'):
                rc = obj

            if rc is None:
                raise ValueError(f"First argument of '{func.__name__}' must be either an instance of {RedisClient.__name__}, an object that contains a 'rc' attribute, or a Redis-like object with 'incr' and 'expire' methods")

            async def sub_wrapper() -> T:
                now = aware_utcnow()

                # --- min_interval gate ---
                if min_interval > 0:
                    last_call_key = Namespace.RATE_LIMIT_LAST_CALL.hash_name(int(now.timestamp()))
                    last_ts_raw = await rc.get(last_call_key)
                    if last_ts_raw is not None:
                        last_ts = float(last_ts_raw)
                        elapsed = (now.timestamp() - last_ts)
                        if elapsed < min_interval:
                            sleep_for = min_interval - elapsed
                            logger.debug(
                                f"Rate limit min_interval: sleeping {sleep_for:.2f}s "
                                f"(last call {last_ts}, now {now.timestamp()})"
                            )
                            await asyncio.sleep(sleep_for)
                            now = aware_utcnow()

                    await rc.set(last_call_key, str(now.timestamp()), ex=int(window_size))

                # --- window counter gate ---
                if limit_per_window > 0:
                    window_start = now.replace(second=0, microsecond=0)
                    window_end = window_start + timedelta(seconds=window_size)
                    window_delta_seconds = int((window_end - now).total_seconds() + 1)
                    counter_hash_name = Namespace.RATE_LIMIT_COUNTER.hash_name(int(window_start.timestamp()))

                    current_count = await rc.incr(counter_hash_name)
                    if current_count == 1:
                        await rc.expire(counter_hash_name, window_delta_seconds)

                    if current_count > limit_per_window:
                        if not auto_retry:
                            raise RateLimitExceededError(
                                next_window=window_end,
                                last_call_timestamp=now.timestamp(),
                            )

                        logger.info(
                            f"Rate limit window exceeded for {func.__name__}: "
                            f"{current_count}/{limit_per_window} calls in window, "
                            f"retrying in {window_delta_seconds}s"
                        )
                        await asyncio.sleep(window_delta_seconds)
                        return await sub_wrapper()

                return await func(*args, **kwargs)

            return await sub_wrapper()

        return wrapper

    return decorator
