from typing import Optional

from app.oauth import OAuth
from app.redis import Namespace, RedisClient

from .dependencies import get_redis_client

STATE_EXPIRES_IN = 300


async def search(rc: Optional[RedisClient] = None):
    if rc is None:
        rc = await get_redis_client()

    oauth = OAuth()
    authorization_url, state = oauth.create_authorization_url()

    state_hash_name = Namespace.CSRF_STATE.hash_name(state)
    await rc.set(state_hash_name, "valid", ex=STATE_EXPIRES_IN)

    data = {
        "authorization_url": authorization_url,
        "state": state
    }

    return data, 200, {"Content-Type": "application/json"}
