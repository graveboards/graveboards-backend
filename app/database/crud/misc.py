"""Miscellaneous status queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.database.status import StatusTarget, get_summary_status

from .decorators import session_manager

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class Misc:
    """Status and diagnostics endpoint."""

    @session_manager()
    async def status(
        self, target: StatusTarget = "summary", session: AsyncSession | None = None
    ) -> dict:
        """Return database status for ``target``."""
        if target == "summary":
            assert session is not None
            return await get_summary_status(session)

        return {"target": target, "error": f"Status target '{target}' is not yet implemented"}
