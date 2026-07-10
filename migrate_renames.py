"""
Database migration: Rename queue_restrictions → queue_rules and restriction_type → type.

This migration updates the database schema to match the renamed model:
  - Table: queue_restrictions → queue_rules
  - Column: restriction_type → type

Run with:
  python migrate_renames.py
"""
import asyncio
import sys

from sqlalchemy import text

from app.database import PostgresqlDB
from app.bootstrap import SetupRunner
from app.config import CONFIG
from app.logging import setup_logging, get_logger


MIGRATION_SQL = """
-- Rename column first (safer than renaming table with dependent objects)
ALTER TABLE queue_restrictions RENAME COLUMN restriction_type TO type;

-- Rename table
ALTER TABLE queue_restrictions RENAME TO queue_rules;
"""


REVERSAL_SQL = """
-- Reverse: rename table first
ALTER TABLE queue_rules RENAME TO queue_restrictions;

-- Reverse: rename column
ALTER TABLE queue_restrictions RENAME COLUMN type TO restriction_type;
"""


async def migrate():
    logger = get_logger("migrate_renames")
    logger.info("Starting schema migration: queue_restrictions → queue_rules")

    db = PostgresqlDB()

    try:
        # Verify table exists
        async with db.session() as session:
            result = await session.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'queue_restrictions')")
            )
            table_exists = result.scalar()

        if not table_exists:
            logger.warning("Table 'queue_restrictions' not found. Migration may have already been applied.")
            return

        # Execute migration
        async with db.engine.connect() as conn:
            await conn.execute(text(MIGRATION_SQL))
            await conn.commit()

        logger.info("Migration completed successfully!")
        logger.info("  - Column 'restriction_type' renamed to 'type'")
        logger.info("  - Table 'queue_restrictions' renamed to 'queue_rules'")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await db.close()


async def rollback():
    """Roll back the migration (use with caution)."""
    logger = get_logger("migrate_renames_rollback")
    logger.warning("Rolling back migration: queue_rules → queue_restrictions")

    db = PostgresqlDB()

    try:
        # Verify table exists
        async with db.session() as session:
            result = await session.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'queue_rules')")
            )
            table_exists = result.scalar()

        if not table_exists:
            logger.warning("Table 'queue_rules' not found. Rollback may have already been applied.")
            return

        # Execute rollback
        async with db.engine.connect() as conn:
            await conn.execute(text(REVERSAL_SQL))
            await conn.commit()

        logger.info("Rollback completed successfully!")
        logger.info("  - Table 'queue_rules' renamed to 'queue_restrictions'")
        logger.info("  - Column 'type' renamed to 'restriction_type'")

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(SetupRunner(CONFIG.bootstrap).run(steps=["create_database"]))

    action = sys.argv[1] if len(sys.argv) > 1 else "migrate"

    if action == "migrate":
        asyncio.run(migrate())
    elif action == "rollback":
        asyncio.run(rollback())
    else:
        print(f"Unknown action: {action}")
        print("Usage: python migrate_renames.py [migrate|rollback]")
        sys.exit(1)
