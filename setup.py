import asyncio
import logging
from datetime import timedelta

from app.redis import RedisClient
from app.database import PostgresqlDB
from app.database.enums import RoleName
from app.database.models import ApiKey, ScoreFetcherTask, User, Role, Queue
from app.security.api_key import generate_api_key
from app.utils import aware_utcnow
from app.logging import setup_logging
from app.config import ADMIN_USER_IDS, MASTER_QUEUE_NAME, MASTER_QUEUE_DESCRIPTION, PRIMARY_ADMIN_USER_ID, PRIVILEGED_USER_IDS


async def setup():
    setup_logging()
    logger = logging.getLogger("maintenance")

    rc = RedisClient()
    db = PostgresqlDB()

    await rc.flushdb()
    await db.create_database()

    if await db.is_empty():
        async with db.session() as session:
            admin_role, privileged_role = await db.add_many(
                Role,
                {"name": RoleName.ADMIN.value},
                {"name": RoleName.PRIVILEGED.value},
                session=session
            )

            def get_roles(user_id: int) -> list:
                roles_ = []

                if user_id in ADMIN_USER_IDS:
                    roles_.append(admin_role)

                if user_id in PRIVILEGED_USER_IDS:
                    roles_.append(privileged_role)

                return roles_

            user_roles_mapping = {user_id: get_roles(user_id) for user_id in ADMIN_USER_IDS | PRIVILEGED_USER_IDS}

            for user_id, roles in user_roles_mapping.items():
                await db.add(User, id=user_id, roles=roles, session=session)

                await db.update_score_fetcher_task(score_fetcher_task.id, enabled=True)
                score_fetcher_task = await db.get(ScoreFetcherTask, user_id=user_id)

                if user_id in ADMIN_USER_IDS:
                    expires_at = aware_utcnow() + timedelta(weeks=1)
                    await db.add(ApiKey, key=generate_api_key(), user_id=user_id, expires_at=expires_at, session=session)

            queue_data = [
                {"user_id": PRIMARY_ADMIN_USER_ID, "name": MASTER_QUEUE_NAME, "description": MASTER_QUEUE_DESCRIPTION},
                {"user_id": 5099768, "name": "Net0's BN Queue", "description": "Net0's BN modding queue"}
            ]

            await db.add_many(Queue, *queue_data, session=session)

        logger.debug(f"Fresh database set up successfully!")

    logger.debug(f"Primary admin user ID: {PRIMARY_ADMIN_USER_ID}")
    logger.debug(f"Primary API key: {(await db.get(ApiKey, user_id=PRIMARY_ADMIN_USER_ID)).key}")

    await rc.aclose()
    await db.close()

if __name__ == "__main__":
    asyncio.run(setup())
