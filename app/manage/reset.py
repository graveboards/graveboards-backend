from app.database import PostgresqlDB, db_lifespan
from app.database.seeding import SeedTarget
from app.setup import setup
from app.logging import get_logger
from .seed import cmd_seed


@db_lifespan
async def cmd_reset(db: PostgresqlDB, seed_target: SeedTarget = None):
    logger = get_logger(__name__)
    steps = 2 if not seed_target else 3

    await db.recreate_database()
    logger.info(f"(1/{steps}) Database cleared")

    await setup(db=db)
    logger.info(f"(2/{steps}) Database set-up")

    if seed_target:
        await cmd_seed(db, seed_target)
        logger.info(f"(3/{steps}) Database seeded")
