import time
from typing import Optional, Tuple

from app.redis import RedisClient


class AuthRateLimiter:
    """Rate limiter for authentication endpoints.

    Limits: 10 requests/minute per IP, hard lockout after 20 failures/hour per IP.
    """

    WINDOW_SIZE = 60
    MAX_REQUESTS = 10
    FAILURE_LOCKOUT = 3600
    MAX_FAILURES = 20

    def __init__(self, rc: RedisClient):
        self.rc = rc

    async def check(self, ip: str) -> Tuple[bool, Optional[int]]:
        """Check if request is allowed.

        Returns: (allowed, retry_after_seconds)
        """
        lockout_key = f"auth_lockout:{ip}"
        lockout_remaining = await self.rc.ttl(lockout_key)
        if lockout_remaining > 0:
            return False, lockout_remaining

        window_key = f"auth_window:{ip}:{int(time.time() // self.WINDOW_SIZE)}"
        current = await self.rc.incr(window_key)
        if current == 1:
            await self.rc.expire(window_key, self.WINDOW_SIZE)

        if current > self.MAX_REQUESTS:
            return False, self.WINDOW_SIZE - (int(time.time()) % self.WINDOW_SIZE)

        return True, None

    async def record_failure(self, ip: str):
        """Record a failed auth attempt. Locks out after MAX_FAILURES."""
        fail_key = f"auth_failures:{ip}"
        failures = await self.rc.incr(fail_key)
        if failures == 1:
            await self.rc.expire(fail_key, self.FAILURE_LOCKOUT)

        if failures >= self.MAX_FAILURES:
            lockout_key = f"auth_lockout:{ip}"
            await self.rc.set(lockout_key, "1", ex=self.FAILURE_LOCKOUT)

    async def record_success(self, ip: str):
        """Record a successful auth. Clears failure counter."""
        await self.rc.delete(f"auth_failures:{ip}")
