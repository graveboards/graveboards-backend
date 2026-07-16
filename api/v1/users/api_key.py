from connexion import request

from app.database import PostgresqlDB
from app.database.models import ApiKey, User
from app.database.enums import RoleName
from app.exceptions import NotFound
from app.security import role_authorization
from app.security.api_key import generate_api_key, hash_api_key
from app.security.overrides import matching_user_id_override
from app.utils import aware_utcnow
from datetime import timedelta
from app.logging import get_logger

logger = get_logger(__name__)


@role_authorization(
    RoleName.ADMIN, override=matching_user_id_override
)
async def get(user_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    key = await db.get(ApiKey, user_id=user_id, is_revoked=False)
    if not key:
        return {"message": "No active API key"}, 200, {"Content-Type": "application/json"}

    return {
        "created_at": key.created_at.isoformat(),
        "expires_at": key.expires_at.isoformat(),
        "is_revoked": key.is_revoked,
    }, 200, {"Content-Type": "application/json"}


@role_authorization(
    RoleName.ADMIN, override=matching_user_id_override
)
async def post(user_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    user = await db.get(User, id=user_id)
    if not user:
        raise NotFound(f"User with ID '{user_id}' not found")

    existing = await db.get(ApiKey, user_id=user_id, is_revoked=False)
    if existing:
        await db.update(ApiKey, existing.id, is_revoked=True)

    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)
    expires_at = aware_utcnow() + timedelta(days=90)

    await db.add(
        ApiKey,
        hashed_key=hashed,
        user_id=user_id,
        expires_at=expires_at,
        is_revoked=False,
    )

    logger.info(f"Rotated API key for user {user_id}")

    return {
        "message": "API key rotated successfully",
        "raw_key": raw_key,
        "expires_at": expires_at.isoformat(),
    }, 200, {"Content-Type": "application/json"}
