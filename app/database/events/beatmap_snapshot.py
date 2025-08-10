from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select, func, insert, update
from sqlalchemy.orm.mapper import Mapper

from app.database.models import BeatmapSnapshot, BeatmapListing

__all__ = [
    "beatmap_snapshot_before_insert",
    "beatmap_snapshot_after_insert"
]


@event.listens_for(BeatmapSnapshot, "before_insert")
def beatmap_snapshot_before_insert(mapper: Mapper[BeatmapSnapshot], connection: Connection, target: BeatmapSnapshot):
    select_stmt = (
        select(func.max(BeatmapSnapshot.snapshot_number))
        .where(BeatmapSnapshot.beatmap_id == target.beatmap_id)
    )

    latest_snapshot = connection.scalar(select_stmt)
    target.snapshot_number = (latest_snapshot or 0) + 1


@event.listens_for(BeatmapSnapshot, "after_insert")
def beatmap_snapshot_after_insert(mapper: Mapper[BeatmapSnapshot], connection: Connection, target: BeatmapSnapshot):
    select_stmt = (
        select(BeatmapListing.id)
        .where(BeatmapListing.beatmap_id == target.beatmap_id)
    )

    beatmap_listing_id = connection.scalar(select_stmt)

    if not beatmap_listing_id:
        stmt = (
            insert(BeatmapListing)
            .values(beatmap_id=target.beatmap_id, beatmap_snapshot_id=target.id)
        )
    else:
        stmt = (
            update(BeatmapListing)
            .where(BeatmapListing.id == beatmap_listing_id)
            .values(beatmap_snapshot_id=target.id)
        )

    connection.execute(stmt)
