"""Authentication rate limiting with Redis."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from app.observability.metrics.auth import (
    auth_lockouts_total,
    auth_rate_limit_checks_total,
)

if TYPE_CHECKING:
    from app.redis_client import RedisClient


def extract_client_ip(request: Any) -> str:
    """Resolve the real client IP for auth rate limiting.

    Reads the ``X-Real-IP`` header forwarded by the frontend (which derives it
    from Traefik's ``X-Forwarded-For``). Without this, every login would be
    keyed on the frontend container's IP because the frontend reaches the
    backend via container-to-container networking, collapsing all users into a
    single rate-limit bucket. The header is only settable by containers on the
    internal ``app`` network, so it is trusted. Falls back to the direct peer.

    Args:
        request:
            The active Connexion/Starlette request.

    Returns:
        The client IP address to key rate limiting on.
    """
    forwarded = request.headers.get("X-Real-IP")
    if forwarded:
        return str(forwarded.split(",")[-1].strip())
    return str(request.client.host) if request.client is not None else "unknown"


class AuthRateLimiter:
    """Rate limiter for authentication endpoints.

    Limits: 10 requests/minute per IP, hard lockout after 20 failures/hour per IP.
    """

    WINDOW_SIZE = 60
    MAX_REQUESTS = 10
    FAILURE_LOCKOUT = 3600
    MAX_FAILURES = 20

    def __init__(self, rc: RedisClient):
        """Initialize the auth rate limiter.

        Args:
            rc:
                Redis client for state storage.
        """
        self.rc = rc

    async def check(self, ip: str) -> tuple[bool, int | None]:
        """Check if a request from the given IP is allowed.

        Args:
            ip:
                The client IP address.

        Returns:
            Tuple of (allowed, retry_after_seconds).
        """
        lockout_key = f"auth_lockout:{ip}"
        lockout_remaining = await self.rc.ttl(lockout_key)
        if lockout_remaining > 0:
            auth_rate_limit_checks_total.labels(result="locked_out").inc()
            return False, lockout_remaining

        window_key = f"auth_window:{ip}:{int(time.time() // self.WINDOW_SIZE)}"
        current = await self.rc.incr(window_key)
        if current == 1:
            await self.rc.expire(window_key, self.WINDOW_SIZE)

        if current > self.MAX_REQUESTS:
            auth_rate_limit_checks_total.labels(result="rate_limited").inc()
            return False, self.WINDOW_SIZE - (int(time.time()) % self.WINDOW_SIZE)

        auth_rate_limit_checks_total.labels(result="allowed").inc()
        return True, None

    async def record_failure(self, ip: str) -> None:
        """Record a failed auth attempt. Locks out after MAX_FAILURES.

        Args:
            ip:
                The client IP address.
        """
        fail_key = f"auth_failures:{ip}"
        failures = await self.rc.incr(fail_key)
        if failures == 1:
            await self.rc.expire(fail_key, self.FAILURE_LOCKOUT)

        if failures >= self.MAX_FAILURES:
            lockout_key = f"auth_lockout:{ip}"
            await self.rc.set(lockout_key, "1", ex=self.FAILURE_LOCKOUT)
            auth_lockouts_total.inc()

    async def record_success(self, ip: str) -> None:
        """Record a successful auth. Clears failure counter.

        Args:
            ip:
                The client IP address.
        """
        await self.rc.delete(f"auth_failures:{ip}")
