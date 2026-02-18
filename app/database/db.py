from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator

from sqlalchemy import event
from sqlalchemy.sql import select
from sqlalchemy.pool.base import ConnectionPoolEntry
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from asyncpg.connection import Connection

from app.config import POSTGRESQL_CONFIGURATION
from app.logging import get_logger
from .crud import CRUD
from . import events

DATABASE_URI = URL.create(**POSTGRESQL_CONFIGURATION)
logger = get_logger(__name__)


class PostgresqlDB(CRUD):
    """Asynchronous PostgreSQL database adapter.

    Wraps SQLAlchemy's ``AsyncEngine`` and provides:
        - Engine lifecycle management
        - Async session factory
        - Transaction-scoped session context manager

    Integrates all ``CRUD`` operations for a fully-featured database interface.

    Designed to centralize database concerns behind a thin, composable abstraction.
    """
    def __init__(self):
        """Initialize the async engine and register connection hooks."""
        self.engine: AsyncEngine = create_async_engine(DATABASE_URI)

        @event.listens_for(self.engine.sync_engine, "first_connect")
        def on_connect(dbapi_connection: Connection, connection_record: ConnectionPoolEntry):
            logger.info(f"Connected to PostgreSQL at '{DATABASE_URI}'")

    def async_session_generator(self) -> async_sessionmaker[AsyncSession]:
        """Return a configured async session factory.

        Sessions are created with ``expire_on_commit=False`` to prevent attribute
        invalidation after transaction commits.

        Returns:
            An ``async_sessionmaker`` bound to this engine.
        """
        return async_sessionmaker(self.engine, expire_on_commit=False)

    async def close(self):
        """Dispose of the underlying engine and release pooled connections."""
        await self.engine.dispose()

    async def test_connection(self):
        """Verify database connectivity.

        Executes a lightweight `SELECT 1` to ensure the database is reachable and
        operational.

        Raises:
            SQLAlchemyError:
                If the connection or query fails.

        Side Effects:
            Disposes of the engine after the test completes.
        """
        try:
            async with self.engine.connect() as conn:
                await conn.execute(select(1))

        except SQLAlchemyError:
            raise
        finally:
            await self.close()

    @asynccontextmanager
    async def session(self, autoflush: bool = True) -> AsyncIterator[AsyncSession]:
        """Provide a transactional async session context.

        Commits on successful exit and rolls back on exception.

        Args:
            autoflush:
                Whether SQLAlchemy should autoflush pending changes.

        Yields:
            AsyncSession: Active transactional session.

        Raises:
            Exception:
                Re-raises any exception after rolling back.
        """
        new_async_session = self.async_session_generator()

        async with new_async_session(autoflush=autoflush) as session_:
            try:
                yield session_
                await session_.commit()
            except Exception:
                await session_.rollback()
                raise
