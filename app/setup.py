import hashlib
from datetime import timedelta

from app.redis import RedisClient
from app.database import PostgresqlDB
from app.database.enums import RoleName
from app.database.models import ApiKey, ScoreFetcherTask, User, Role, Queue
from app.security.api_key import generate_api_key, hash_api_key
from app.utils import aware_utcnow
from app.logging import get_logger
from app.config import (
    ADMIN_USER_IDS,
    DEBUG,
    DEBUG_API_KEY,
    JWT_SECRET_KEY,
    MASTER_QUEUE_NAME,
    MASTER_QUEUE_DESCRIPTION,
    PRIMARY_ADMIN_USER_ID
)


def get_debug_api_key() -> str:
    if DEBUG_API_KEY:
        return DEBUG_API_KEY

    seed = f"{JWT_SECRET_KEY}:{PRIMARY_ADMIN_USER_ID}:debug-api-key"
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


async def setup(rc: RedisClient = None, db: PostgresqlDB = None):
    logger = get_logger(__name__)
    primary_raw_key = None

    if rc is None:
        rc = RedisClient()

    if db is None:
        db = PostgresqlDB()

    await rc.flushdb()
    await db.create_database()

    if await db.is_empty():
        async with db.session(autoflush=False) as session:
            admin_role, = await db.add_many(
                Role,
                {"name": RoleName.ADMIN.value},
                session=session
            )

            def get_roles(user_id: int) -> list:
                roles_ = []

                if user_id in ADMIN_USER_IDS:
                    roles_.append(admin_role)

                return roles_

            user_roles_mapping = {user_id: get_roles(user_id) for user_id in ADMIN_USER_IDS}

            for user_id, roles in user_roles_mapping.items():
                await db.add(User, id=user_id, roles=roles, session=session)

                score_fetcher_task = await db.get(ScoreFetcherTask, user_id=user_id, session=session)
                await db.update(ScoreFetcherTask, score_fetcher_task.id, enabled=True, session=session)

                if user_id in ADMIN_USER_IDS:
                    raw_key = generate_api_key()
                    expires_at = aware_utcnow() + timedelta(weeks=1)
                    await db.add(ApiKey, hashed_key=hash_api_key(raw_key), user_id=user_id, expires_at=expires_at, session=session)

                    if user_id == PRIMARY_ADMIN_USER_ID:
                        primary_raw_key = raw_key

            queue_data = [
                {"user_id": PRIMARY_ADMIN_USER_ID, "name": MASTER_QUEUE_NAME, "description": MASTER_QUEUE_DESCRIPTION},
                {"user_id": 5099768, "name": "Net0's BN Queue", "description": "Net0's BN modding queue"}
            ]

            await db.add_many(Queue, *queue_data, session=session)

        logger.debug(f"Fresh database set up successfully!")

    if DEBUG:
        primary_raw_key = get_debug_api_key()
        hashed_key = hash_api_key(primary_raw_key)
        expires_at = aware_utcnow() + timedelta(weeks=1)

        async with db.session() as session:
            primary_admin = await db.get(User, id=PRIMARY_ADMIN_USER_ID, session=session)

            if primary_admin is None:
                logger.warning(f"Unable to set debug API key; primary admin user {PRIMARY_ADMIN_USER_ID} does not exist")
                primary_raw_key = None
            else:
                api_key = await db.get(ApiKey, hashed_key=hashed_key, session=session)

                if api_key is None:
                    await db.add(ApiKey, hashed_key=hashed_key, user_id=PRIMARY_ADMIN_USER_ID, expires_at=expires_at, session=session)
                else:
                    await db.update(
                        ApiKey,
                        api_key.id,
                        user_id=PRIMARY_ADMIN_USER_ID,
                        expires_at=expires_at,
                        is_revoked=False,
                        session=session
                    )

    logger.debug(f"Primary admin user ID: {PRIMARY_ADMIN_USER_ID}")
    if primary_raw_key is not None:
        logger.debug(f"Primary API key: {primary_raw_key}")
    else:
        logger.debug("Primary API key is not available")

    await rc.aclose()
    await db.close()
