from authlib.integrations.base_client.errors import OAuthError
from connexion import request
from jwt.exceptions import InvalidIssuerError, ExpiredSignatureError, InvalidTokenError

from app.database import PostgresqlDB
from app.database.models import User, ScoreFetcherTask, OAuthToken
from app.exceptions import BadRequest, OsuOAuthError
from app.oauth import OAuth
from app.osu_api import OsuAPIClient
from app.redis import RedisClient, Namespace
from app.security import create_token_payload, encode_token, validate_token


async def search(token: str):
    try:
        jwt_claims = validate_token(token)
    except (InvalidTokenError, ExpiredSignatureError, InvalidIssuerError):
        raise BadRequest("Invalid or expired JWT")

    return jwt_claims, 200, {"Content-Type": "application/json"}


async def post(body: dict):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    code = body.get("code")
    state = body.get("state")

    if not code:
        raise BadRequest("Missing code in body")

    if not state:
        raise BadRequest("Missing state in body")

    state_hash_name = Namespace.CSRF_STATE.hash_name(state)
    stored_state = await rc.getdel(state_hash_name)

    if not stored_state or stored_state != "valid":
        raise BadRequest("Invalid or expired state")

    try:
        oauth = OAuth()
        token = await oauth.fetch_token(
            grant_type="authorization_code",
            scope="public identify",
            code=code
        )
        access_token = token["access_token"]
        refresh_token = token["refresh_token"]
        expires_at = token["expires_at"]
    except OAuthError as e:
        raise OsuOAuthError(e)

    oac = OsuAPIClient(rc)
    user_data = await oac.get_own_data(access_token)
    user_id = user_data["id"]

    if not await db.get(User, id=user_id):
        await db.add(User, id=user_id)

    score_fetcher_task = await db.get(ScoreFetcherTask, user_id=user_id)

    if not score_fetcher_task.enabled and score_fetcher_task.last_fetch is None:
        await db.update(ScoreFetcherTask, score_fetcher_task.id, enabled=True)

    await db.add(
        OAuthToken,
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )

    payload = create_token_payload(user_id)
    jwt_ = encode_token(payload)

    return {"token": jwt_}, 201, {"Content-Type": "application/json"}
