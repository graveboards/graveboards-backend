from typing import Optional

from connexion import request
from connexion.exceptions import TooManyRequests

from app.oauth import OAuth
from app.redis import Namespace, RedisClient
from app.security.auth_rate_limit import AuthRateLimiter

from .dependencies import get_redis_client

__all__ = ["search"]

STATE_EXPIRES_IN = 300


async def search(rc: Optional[RedisClient] = None):
    if rc is None:
        rc = await get_redis_client()

    client_ip = request.client.host if hasattr(request, 'client') else "unknown"
    limiter = AuthRateLimiter(rc)
    allowed, retry_after = await limiter.check(client_ip)
    if not allowed:
        raise TooManyRequests(f"Too many requests. Try again in {retry_after}s")

    oauth = OAuth()
    authorization_url, state = oauth.create_authorization_url()

    state_hash_name = Namespace.CSRF_STATE.hash_name(state)
    await rc.set(state_hash_name, "valid", ex=STATE_EXPIRES_IN)

    await limiter.record_success(client_ip)

    data = {
        "authorization_url": authorization_url,
        "state": state
    }

    return data, 200, {"Content-Type": "application/json"}
