from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select, func
from sqlalchemy.orm.mapper import Mapper

from app.database.models import BeatmapSnapshot

__all__ = [
    "beatmap_snapshot_before_insert"
]


@event.listens_for(BeatmapSnapshot, "before_insert")
def beatmap_snapshot_before_insert(mapper: Mapper[BeatmapSnapshot], connection: Connection, target: BeatmapSnapshot):
    select_stmt = (
        select(func.max(BeatmapSnapshot.snapshot_number))
        .where(BeatmapSnapshot.beatmap_id == target.beatmap_id)
    )

    latest_snapshot = connection.scalar(select_stmt)
    target.snapshot_number = (latest_snapshot or 0) + 1
