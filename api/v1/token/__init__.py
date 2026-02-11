from authlib.integrations.base_client.errors import OAuthError
from connexion import request

from app.database import PostgresqlDB
from app.database.models import JWT, User, ScoreFetcherTask, OAuthToken
from app.database.schemas import JWTSchema
from app.exceptions import NotFound, BadRequest, OsuOAuthError
from app.oauth import OAuth
from app.osu_api import OsuAPIClient
from app.redis import RedisClient, Namespace
from app.security import create_token_payload, encode_token


async def search(token: str):
    db: PostgresqlDB = request.state.db

    jwt = await db.get(JWT, token=token)

    if not jwt:
        raise NotFound(f"The JWT provided does not exist")

    jwt_data = JWTSchema.model_validate(jwt).model_dump(
        exclude={"id", "updated_at"}
    )

    return jwt_data, 200, {"Content-Type": "application/json"}


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
    jwt_str = encode_token(payload)
    jwt = await db.add(
        JWT,
        user_id=user_id,
        token=jwt_str,
        issued_at=payload["iat"],
        expires_at=payload["exp"]
    )
    jwt_data = JWTSchema.model_validate(jwt).model_dump(
        exclude={"id", "updated_at"}
    )

    return jwt_data, 201, {"Content-Type": "application/json"}
