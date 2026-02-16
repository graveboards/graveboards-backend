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
        match target:
            case "summary":
                return await get_summary_status(session)
            case "users":
                raise NotImplementedError
            case "beatmaps":
                raise NotImplementedError
            case "beatmapsets":
                raise NotImplementedError
            case "queues":
                raise NotImplementedError
            case "requests":
                raise NotImplementedError
            case _:
                raise NotImplementedError
