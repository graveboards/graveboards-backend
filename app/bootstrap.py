import hashlib
import secrets
from datetime import timedelta

from app.redis import RedisClient, Namespace
from app.database import PostgresqlDB
from app.database.models import ApiKey, ScoreFetcherTask, User, Role, Queue
from app.security.api_key import generate_api_key, hash_api_key
from app.utils import aware_utcnow
from app.logging import get_logger
from app.config import BootstrapConfig, DEBUG, DEBUG_API_KEY, JWT_SECRET_KEY


def _get_debug_api_key() -> str:
    if DEBUG_API_KEY:
        return DEBUG_API_KEY

    seed = f"{JWT_SECRET_KEY}:{secrets.token_hex(8)}:debug-api-key"
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


class SetupRunner:
    """Composable database bootstrap runner.

    Each method corresponds to a single setup step. Steps can be run
    individually or together via :meth:`run`.
    """

    def __init__(
        self,
        config: BootstrapConfig,
        db: PostgresqlDB = None,
        rc: RedisClient = None,
    ):
        self.config = config
        self.db = db or PostgresqlDB()
        self.rc = rc or RedisClient()

    async def create_database(self):
        """Create the database if it does not exist."""
        await self.db.create_database()

    async def seed_roles(self):
        """Create roles defined in config.initial_roles."""
        logger = get_logger(__name__)
        roles_to_create = []

        async with self.db.session(autoflush=False) as session:
            for role_name in self.config.initial_roles:
                existing = await self.db.get(Role, name=role_name, session=session)

                if existing is None:
                    roles_to_create.append({"name": role_name})

            if roles_to_create:
                await self.db.add_many(Role, *roles_to_create, session=session)
                logger.debug(f"Created {len(roles_to_create)} role(s)")

    async def seed_users(self):
        """Create initial users with their roles and optional score fetcher tasks."""
        logger = get_logger(__name__)

        async with self.db.session(autoflush=False) as session:
            role_lookup = {}

            for role in await self.db.get_many(Role, session=session):
                role_lookup[role.name] = role

            for user_cfg in self.config.initial_users:
                existing_user = await self.db.get(User, id=user_cfg.user_id, session=session)

                if existing_user is None:
                    user_roles = [role_lookup[name] for name in user_cfg.roles if name in role_lookup]
                    await self.db.add(User, id=user_cfg.user_id, roles=user_roles, session=session)
                    logger.debug(f"Created user: {user_cfg.user_id}")

                score_fetcher = await self.db.get(
                    ScoreFetcherTask, user_id=user_cfg.user_id, session=session
                )

                if score_fetcher is None and user_cfg.enable_score_fetcher:
                    await self.db.add(
                        ScoreFetcherTask,
                        user_id=user_cfg.user_id,
                        enabled=True,
                        session=session,
                    )
                    logger.debug(f"Enabled score fetcher for user: {user_cfg.user_id}")

    async def seed_api_keys(self):
        """Generate API keys for users with generate_api_key=True."""
        logger = get_logger(__name__)

        async with self.db.session(autoflush=False) as session:
            for user_cfg in self.config.initial_users:
                if not user_cfg.generate_api_key:
                    continue

                existing_key = await self.db.get(ApiKey, user_id=user_cfg.user_id, session=session)

                if existing_key is not None:
                    continue

                expires_at = aware_utcnow() + timedelta(weeks=1)
                raw_key = generate_api_key()
                await self.db.add(
                    ApiKey,
                    hashed_key=hash_api_key(raw_key),
                    user_id=user_cfg.user_id,
                    expires_at=expires_at,
                    session=session,
                )
                logger.debug(f"Generated API key for user: {user_cfg.user_id}")

    async def seed_queues(self):
        """Create the master queue and any extra queues from config."""
        logger = get_logger(__name__)
        queue_data = []

        if self.config.master_queue.user_id:
            queue_data.append({
                "user_id": self.config.master_queue.user_id,
                "name": self.config.master_queue.name,
                "description": self.config.master_queue.description,
            })

        for extra in self.config.extra_queues:
            if extra.user_id:
                queue_data.append({
                    "user_id": extra.user_id,
                    "name": extra.name,
                    "description": extra.description,
                })

        if queue_data:
            await self.db.add_many(Queue, *queue_data)
            logger.debug(f"Created {len(queue_data)} queue(s)")

    async def cleanup_stale_tasks(self) -> int:
        """Remove orphaned queue request handler tasks from Redis.

        Orphaned tasks are tasks that were never marked as completed or failed,
        typically left behind after a daemon crash. These tasks can be safely
        deleted as they will be re-submitted if needed.

        Returns:
            Number of tasks cleaned up.
        """
        logger = get_logger(__name__)
        cleaned = 0

        task_pattern = f"{Namespace.QUEUE_REQUEST_HANDLER_TASK.value}:*"
        task_hash_names = await self.rc.paginate_scan(task_pattern, type_="HASH")

        for task_hash_name in task_hash_names:
            task_data = await self.rc.hgetall(task_hash_name)

            completed_at = task_data.get("completed_at")
            failed_at = task_data.get("failed_at")

            if not completed_at and not failed_at:
                await self.rc.delete(task_hash_name)
                cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} stale queue request handler task(s)")

        return cleaned

    async def run(self, steps: list[str] = None):
        """Run specified setup steps (or all from config if none given).

        Args:
            steps:
                List of step names to run. If None, runs all steps from config.
        """
        for step_name in steps or self.config.setup_steps:
            method = getattr(self, step_name, None)

            if method is None:
                raise ValueError(f"Unknown setup step: '{step_name}'")

            await method()

    async def close(self):
        """Close database and Redis connections."""
        await self.rc.aclose()
        await self.db.close()


async def _setup_debug_api_key(rc: RedisClient = None, db: PostgresqlDB = None):
    """Set up debug API key for development mode."""
    logger = get_logger(__name__)
    rc = rc or RedisClient()
    db = db or PostgresqlDB()
    primary_admin_id = None

    if not DEBUG:
        await rc.aclose()
        await db.close()
        return None

    primary_raw_key = _get_debug_api_key()
    hashed_key = hash_api_key(primary_raw_key)
    expires_at = aware_utcnow() + timedelta(weeks=1)

    async with db.session() as session:
        from app.config import CONFIG
        bootstrap = CONFIG.bootstrap

        if bootstrap.initial_users:
            primary_admin_id = bootstrap.initial_users[0].user_id
        else:
            logger.warning("No initial users configured; cannot set debug API key")
            await rc.aclose()
            await db.close()
            return None

        primary_admin = await db.get(User, id=primary_admin_id, session=session)

        if primary_admin is None:
            logger.warning(f"Unable to set debug API key; primary admin user {primary_admin_id} does not exist")
            await rc.aclose()
            await db.close()
            return None

        api_key = await db.get(ApiKey, hashed_key=hashed_key, session=session)

        if api_key is None:
            await db.add(
                ApiKey,
                hashed_key=hashed_key,
                user_id=primary_admin_id,
                expires_at=expires_at,
                session=session,
            )
        else:
            await db.update(
                ApiKey,
                api_key.id,
                user_id=primary_admin_id,
                expires_at=expires_at,
                is_revoked=False,
                session=session,
            )

    await rc.aclose()
    await db.close()
    return primary_raw_key
