import secrets
import hashlib
from datetime import timedelta

from app.database import PostgresqlDB, db_lifespan
from app.security.api_key import generate_api_key, hash_api_key
from app.database.models import ApiKey, User
from app.utils import aware_utcnow
from app.logging import get_logger


@db_lifespan
async def cmd_generate_api_key(db: PostgresqlDB, user_id: int, expires_days: int = 90):
    """Generate a new API key for an existing user.

    The raw key is printed ONCE to stdout and never stored.
    The SHA-256 hash is stored in the database.
    """
    logger = get_logger(__name__)

    user = await db.get(User, id=user_id)
    if not user:
        raise ValueError(f"User with ID '{user_id}' does not exist")

    existing = await db.get(ApiKey, user_id=user_id, is_revoked=False)
    if existing:
        logger.warning(
            f"User {user_id} already has an active API key "
            f"(expires {existing.expires_at}). Consider rotating instead."
        )

    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)
    expires_at = aware_utcnow() + timedelta(days=expires_days)

    await db.add(
        ApiKey,
        hashed_key=hashed,
        user_id=user_id,
        expires_at=expires_at,
        is_revoked=False,
    )

    logger.info(f"Generated API key for user {user_id}, expires {expires_at}")

    print("=" * 50)
    print("RAW API KEY (copy now, will not be shown again)")
    print(f"  {raw_key}")
    print(f"  Hash: {hashed}")
    print(f"  Expires: {expires_at.isoformat()}")
    print("=" * 50)
    print()
    print("WARNING: This key is only displayed once. Store it securely.")
