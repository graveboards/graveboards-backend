from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import select
from sqlalchemy.sql.functions import func

from app.database.models import Beatmap, Beatmapset, Queue, Request, User


async def get_summary_status(session: AsyncSession) -> dict:
    models = (User, Beatmap, Beatmapset, Queue, Request)
    status = {"target": "summary"}

    for model in models:
        count = await session.scalar(select(func.count()).select_from(model))
        status[model.__tablename__] = count

    return status
