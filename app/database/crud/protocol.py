"""Typed protocol for the database interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


class DatabaseProtocol(Protocol):
    """Minimal interface exposing the engine and session factory."""

    engine: AsyncEngine

    def session(self, autoflush: bool = True) -> AbstractAsyncContextManager[AsyncSession]:
        """Return a transaction-scoped async session context manager."""
        ...
