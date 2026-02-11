import asyncio
import logging
from typing import Callable, Any, Awaitable
from functools import wraps
from datetime import datetime, timedelta

from .rc import RedisClient
from .enums import Namespace
from app.exceptions import RateLimitExceededError

logger = logging.getLogger("redis")


def rate_limit(limit_per_window: int, auto_retry: bool = True):
    def decorator(func: Callable[..., Awaitable[Any]]):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Function '{func.__name__}' must be async to use @rate_limit")

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Awaitable[Any]:
            obj = args[0] if args else None
            rc: RedisClient | None = None

            if obj and isinstance(obj, RedisClient):
                rc = obj
            elif obj and hasattr(obj, "rc"):
                rc = getattr(obj, "rc")

            if rc is None:
                raise ValueError(f"First argument of '{func.__name__}' must be either an instance of {RedisClient.__name__} or an object that contains a {RedisClient.__name__} instance attribute named 'rc'")

            async def sub_wrapper():
                now = datetime.now()
                window_start = now - timedelta(seconds=now.second, microseconds=now.microsecond)
                window_end = window_start + timedelta(minutes=1)
                window_delta_seconds = int((window_end - now).total_seconds() + 1)
                counter_hash_name = Namespace.RATE_LIMIT_COUNTER.hash_name(int(window_start.timestamp()))

                if (current_count := await rc.incr(counter_hash_name)) == 1:
                    await rc.expire(counter_hash_name, window_delta_seconds)

                if current_count > limit_per_window:
                    if not auto_retry:
                        raise RateLimitExceededError(window_end)

                    func_repr = (
                        f"{repr(func)}"
                        f" ({", ".join(str(arg) for arg in args[1:])}"
                        f"{", " if kwargs else ""}"
                        f"{", ".join(["{}={}".format(key, value) for key, value in kwargs.items()])})"
                    )

                    logger.info(f"Rate limited: {func_repr}, retrying in {window_delta_seconds} seconds")
                    await asyncio.sleep(window_delta_seconds)
                    return await sub_wrapper()

                return await func(*args, **kwargs)

            return await sub_wrapper()

        return wrapper

    return decorator
