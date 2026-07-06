import sys
from typing import Optional

from app.database import PostgresqlDB, db_lifespan
from app.database.seeding import SeedTarget
from app.config import CONFIG
from app.bootstrap import SetupRunner
from app.logging import get_logger
from .seed import cmd_seed


@db_lifespan
async def cmd_reset(db: PostgresqlDB, seed_target: Optional[SeedTarget] = None, force: bool = False):
    if not force:
        response = input("This will drop all tables and reset the database. Continue? [y/N]: ")
        if response.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    logger = get_logger(__name__)
    steps = 2 if not seed_target else 3

    await db.recreate_database()
    logger.info(f"(1/{steps}) Database cleared")

    runner = SetupRunner(CONFIG.bootstrap, db=db)
    await runner.run(steps=["seed_roles", "seed_users", "seed_api_keys", "seed_queues"])
    logger.info(f"(2/{steps}) Database set-up")

    if seed_target:
        await cmd_seed(db, seed_target)
        logger.info(f"(3/{steps}) Database seeded")
