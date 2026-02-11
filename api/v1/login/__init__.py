from connexion.context import request

from app.oauth import OAuth
from app.redis import RedisClient, Namespace

STATE_EXPIRES_IN = 300


async def search():
    rc: RedisClient = request.state.rc

    oauth = OAuth()
    authorization_url, state = oauth.create_authorization_url()

    state_hash_name = Namespace.CSRF_STATE.hash_name(state)
    await rc.set(state_hash_name, "valid", ex=STATE_EXPIRES_IN)

    data = {
        "authorization_url": authorization_url,
        "state": state
    }

    return data, 200, {"Content-Type": "application/json"}
