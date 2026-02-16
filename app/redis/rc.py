import asyncio
from contextlib import contextmanager, asynccontextmanager

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
    def __init__(self):
        super().__init__(**REDIS_CONFIGURATION)
        logger.info(f"Connected to Redis at '{REDIS_BASE_URL}'")

    async def paginate_scan(self, pattern: str, limit: int = None, offset: int = 0, type_: str = None) -> list[str]:
        keys = []
        count = 0

        async for key in self.scan_iter(match=pattern, _type=type_):
            if count < offset:
                count += 1
                continue

            if limit is not None and len(keys) >= limit:
                break

            keys.append(key)

        return keys

    @asynccontextmanager
    async def lock_ctx(self, key: str, expiry: int = LOCK_EXPIRY, timeout: float = LOCK_ACQUISITION_TIMEOUT, retry_interval: float = LOCK_ACQUISITION_RETRY_INTERVAL):
        deadline = asyncio.get_event_loop().time() + timeout

        while True:
            if await self.set(key, "locked", ex=expiry, nx=True):
                break

            if asyncio.get_event_loop().time() > deadline:
                raise RedisLockTimeoutError(key, timeout)

            await asyncio.sleep(retry_interval)

        try:
            yield
        finally:
            await self.delete(key)


@contextmanager
def redis_connection():
    from .pool import connection_pool

    rc = Redis(connection_pool=connection_pool)

    try:
        yield rc
    finally:
        rc.close()
