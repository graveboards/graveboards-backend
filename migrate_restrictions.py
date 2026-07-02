import asyncio
import sys

from app.database import PostgresqlDB
from app.logging import setup_logging
from app.setup import setup
from app.logging import get_logger

logger = get_logger("migrate")


async def migrate():
    logger.info("Starting queue_restrictions table migration...")

    db = PostgresqlDB()

    try:
        async with db.engine.begin() as conn:
            result = await conn.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'queue_restrictions')"
            )
            table_exists = result.scalar()

        if table_exists:
            logger.info("queue_restrictions table already exists, skipping")
            return

        async with db.engine.begin() as conn:
            await conn.execute("""
                CREATE TABLE queue_restrictions (
                    id SERIAL PRIMARY KEY,
                    queue_id INTEGER NOT NULL REFERENCES queues(id) ON DELETE CASCADE,
                    restriction_type VARCHAR(50) NOT NULL,
                    config JSON NOT NULL DEFAULT '{}',
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

        logger.info("queue_restrictions table created successfully")
    finally:
        await db.close()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(setup())
    asyncio.run(migrate())
