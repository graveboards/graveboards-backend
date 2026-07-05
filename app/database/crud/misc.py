from sqlalchemy.ext.asyncio import AsyncSession

from app.database.status import StatusTarget, get_summary_status
from .decorators import session_manager


class Misc:
    @session_manager()
    async def status(
        self,
        target: StatusTarget = "summary",
        session: AsyncSession = None
    ) -> dict:
        if target == "summary":
            return await get_summary_status(session)

        return {"target": target, "error": f"Status target '{target}' is not yet implemented"}
