from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select
from sqlalchemy.sql.functions import func
from sqlalchemy.orm.mapper import Mapper

from app.database.models import Request, BeatmapsetSnapshot

__all__ = [
    "request_before_insert"
]


@event.listens_for(Request, "before_insert")
def request_before_insert(mapper: Mapper[Request], connection: Connection, target: Request):
    latest_beatmapset_snapshot_id_stmt = (
        select(func.max(BeatmapsetSnapshot.id))
        .where(BeatmapsetSnapshot.beatmapset_id == target.beatmapset_id)
    )

    latest_beatmapset_snapshot_id = connection.scalar(latest_beatmapset_snapshot_id_stmt)

    if latest_beatmapset_snapshot_id is None:
        raise ValueError(f"No BeatmapsetSnapshot found for beatmapset ID {target.beatmapset_id}")

    target.beatmapset_snapshot_id = latest_beatmapset_snapshot_id
