from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select, insert, update, func
from sqlalchemy.orm.mapper import Mapper

from app.database.models import BeatmapsetSnapshot, BeatmapsetListing

__all__ = [
    "beatmapset_snapshot_before_insert",
    "beatmapset_snapshot_after_insert"
]


@event.listens_for(BeatmapsetSnapshot, "before_insert")
def beatmapset_snapshot_before_insert(mapper: Mapper[BeatmapsetSnapshot], connection: Connection, target: BeatmapsetSnapshot):
    select_stmt = (
        select(func.max(BeatmapsetSnapshot.snapshot_number))
        .where(BeatmapsetSnapshot.beatmapset_id == target.beatmapset_id)
    )

    latest_snapshot = connection.scalar(select_stmt)
    target.snapshot_number = (latest_snapshot or 0) + 1


@event.listens_for(BeatmapsetSnapshot, "after_insert")
def beatmapset_snapshot_after_insert(mapper: Mapper[BeatmapsetSnapshot], connection: Connection, target: BeatmapsetSnapshot):
    select_stmt = (
        select(BeatmapsetListing.id)
        .where(BeatmapsetListing.beatmapset_id == target.beatmapset_id)
    )

    beatmapset_listing_id = connection.scalar(select_stmt)

    if not beatmapset_listing_id:
        stmt = (
            insert(BeatmapsetListing)
            .values(beatmapset_id=target.beatmapset_id, beatmapset_snapshot_id=target.id)
        )
    else:
        stmt = (
            update(BeatmapsetListing)
            .where(BeatmapsetListing.id == beatmapset_listing_id)
            .values(beatmapset_snapshot_id=target.id)
        )

    connection.execute(stmt)
