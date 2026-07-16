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
from app.security.oauth_encryption import encrypt_token
from app.utils import aware_utcnow


async def search(token: str):
    try:
        jwt_claims = validate_token(token)
    except (InvalidTokenError, ExpiredSignatureError, InvalidIssuerError):
        raise BadRequest("Invalid or expired JWT")

    return jwt_claims, 200, {"Content-Type": "application/json"}


async def post(
    body: dict,
    oauth: OAuth = None,
    osu_api_client: OsuAPIClient = None,
    db: PostgresqlDB = None,
    rc: RedisClient = None,
):
    if rc is None:
        rc = request.state.rc
    if db is None:
        db = request.state.db

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
        if oauth is None:
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

    if osu_api_client is None:
        osu_api_client = OsuAPIClient(rc)
    async with osu_api_client:
        user_data = await osu_api_client.get_own_data(access_token)
    user_id = user_data["id"]

    if not await db.get(User, id=user_id):
        await db.add(User, id=user_id)

    score_fetcher_task = await db.get(ScoreFetcherTask, user_id=user_id)

    if not score_fetcher_task.enabled and score_fetcher_task.last_fetch is None:
        await db.update(ScoreFetcherTask, score_fetcher_task.id, enabled=True)

    await db.add(
        OAuthToken,
        user_id=user_id,
        access_token_enc=encrypt_token(access_token),
        refresh_token_enc=encrypt_token(refresh_token),
        expires_at=aware_utcnow()
    )

    payload = create_token_payload(user_id)
    jwt_ = encode_token(payload)

    return {"token": jwt_}, 201, {"Content-Type": "application/json"}
