"""Async PostgreSQL database adapter built on SQLAlchemy.

Provides engine lifecycle management, async session factories, connection
hooks for metrics, and a transaction-scoped session context manager.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy import event
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import select

from app.config import POSTGRESQL_CONFIGURATION
from app.observability.logging import get_logger
from app.observability.metrics.db import (
    classify_query,
    db_pool_checked_in,
    db_pool_checked_out,
    db_pool_overflow,
    db_pool_size,
    db_query_duration_seconds,
)

from . import events  # noqa: F401 (register SQLAlchemy model event listeners)
from .crud import CRUD

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import TracebackType

    from asyncpg.connection import Connection
    from sqlalchemy.pool.base import ConnectionPoolEntry

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

    def __init__(self) -> None:
        """Initialize the async engine and register connection hooks."""
        self.engine: AsyncEngine = create_async_engine(
            DATABASE_URI, pool_size=20, max_overflow=10, pool_recycle=300, pool_pre_ping=True
        )

        self._setup_pool_metrics()
        self._setup_query_metrics()

        @event.listens_for(self.engine.sync_engine, "first_connect")
        def on_connect(
            _dbapi_connection: Connection, _connection_record: ConnectionPoolEntry
        ) -> None:
            logger.debug(f"Connected to PostgreSQL at '{DATABASE_URI}'")

    def _setup_pool_metrics(self) -> None:
        @event.listens_for(self.engine.sync_engine.pool, "checkin")
        def on_checkin(
            _dbapi_connection: Connection, _connection_record: ConnectionPoolEntry
        ) -> None:
            db_pool_checked_out.dec()
            db_pool_checked_in.inc()

        @event.listens_for(self.engine.sync_engine.pool, "checkout")
        def on_checkout(
            _dbapi_connection: Connection, _pid: int, _connection_proxy: Connection
        ) -> None:
            db_pool_checked_out.inc()
            db_pool_checked_in.dec()

        @event.listens_for(self.engine.sync_engine.pool, "connect")
        def on_connect_pool(
            _dbapi_connection: Connection, _connection_record: ConnectionPoolEntry
        ) -> None:
            db_pool_size.set(self.engine.pool.size())  # type: ignore[attr-defined]
            db_pool_overflow.set(max(0, self.engine.sync_engine.pool.overflow()))  # type: ignore[attr-defined]

        db_pool_size.set(self.engine.pool.size())  # type: ignore[attr-defined]

    def _setup_query_metrics(self) -> None:
        import time as _time

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def on_before_cursor_execute(
            _conn: Any,
            _cursor: Any,
            _statement: str,
            _parameters: Any,
            context: Any,
            _executemany: bool,
        ) -> None:
            context._query_start_time = _time.perf_counter()

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def on_after_cursor_execute(
            _conn: Any,
            _cursor: Any,
            statement: str,
            _parameters: Any,
            context: Any,
            _executemany: bool,
        ) -> None:
            start: float | int | None = getattr(context, "_query_start_time", None)
            if start is not None:
                duration = _time.perf_counter() - start
                query_type = classify_query(statement)
                db_query_duration_seconds.labels(query_type=query_type).observe(duration)

    def async_session_generator(self) -> async_sessionmaker[AsyncSession]:
        """Return a configured async session factory.

        Sessions are created with ``expire_on_commit=False`` to prevent attribute
        invalidation after transaction commits.

        Returns:
        -------
            An ``async_sessionmaker`` bound to this engine.
        """
        return async_sessionmaker(self.engine, expire_on_commit=False)

    async def test_connection(self) -> None:
        """Verify database connectivity.

        Executes a lightweight `SELECT 1` to ensure the database is reachable and
        operational. Uses pooled connections without closing the engine.

        Raises:
        ------
            SQLAlchemyError:
                If the connection or query fails.
        """
        async with self.engine.connect() as conn:
            await conn.execute(select(1))

    async def __aenter__(self) -> PostgresqlDB:
        """Context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - dispose engine."""
        await self.close()

    async def close(self) -> None:
        """Close the engine."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self, autoflush: bool = True) -> AsyncIterator[AsyncSession]:
        """Provide a transactional async session context.

        Commits on successful exit and rolls back on exception.

        Args:
            autoflush:
                Whether SQLAlchemy should autoflush pending changes.

        Yields:
        ------
            AsyncSession: Active transactional session.

        Raises:
        ------
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
