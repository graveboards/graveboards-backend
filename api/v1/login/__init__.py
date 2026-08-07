"""Re-exports for the login v1 API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from connexion import request

if TYPE_CHECKING:
    from api.http_types import APIResponse
from app.exceptions import TooManyRequests
from app.oauth import OAuth
from app.redis_client import Namespace, RedisClient
from app.security.auth_rate_limit import AuthRateLimiter

__all__ = ["search"]

STATE_EXPIRES_IN = 300


async def search(rc: RedisClient | None = None) -> APIResponse:
    """Initiate an OAuth login flow.

    Returns:
        Tuple of (authorization URL and state, status code, headers).
    """
    if rc is None:
        rc = request.state.rc

    client_ip = request.client.host if request.client is not None else "unknown"
    limiter = AuthRateLimiter(rc)
    allowed, retry_after = await limiter.check(client_ip)
    if not allowed:
        raise TooManyRequests(f"Too many requests. Try again in {retry_after}s")

    oauth = OAuth()
    authorization_url, state = oauth.create_authorization_url()

    state_hash_name = Namespace.CSRF_STATE.hash_name(state)
    await rc.set(state_hash_name, "valid", ex=STATE_EXPIRES_IN)

    await limiter.record_success(client_ip)

    data = {"authorization_url": authorization_url, "state": state}

    return data, 200, {"Content-Type": "application/json"}
