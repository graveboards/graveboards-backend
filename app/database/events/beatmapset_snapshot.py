from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select, insert, update, func
from sqlalchemy.orm.mapper import Mapper

from app.logging import get_logger
from app.database.models import BeatmapsetSnapshot, BeatmapsetListing, Request

__all__ = [
    "beatmapset_snapshot_before_insert",
    "beatmapset_snapshot_after_insert"
]

logger = get_logger(__name__)


@event.listens_for(BeatmapsetSnapshot, "before_insert")
def beatmapset_snapshot_before_insert(mapper: Mapper[BeatmapsetSnapshot], connection: Connection, target: BeatmapsetSnapshot):
    """Assign the next sequential snapshot number for a ``BeatmapsetSnapshot``.

    Determines the maximum ``snapshot_number`` for the associated ``beatmapset_id`` and
    increments it to ensure per-beatmapset version ordering.

    Args:
        mapper:
            SQLAlchemy mapper for ``BeatmapsetSnapshot``.
        connection:
            Active database connection.
        target:
            The ``BeatmapsetSnapshot`` being inserted.

    Side Effects:
        Mutates ``target.snapshot_number`` prior to persistence.
    """
    select_stmt = (
        select(func.max(BeatmapsetSnapshot.snapshot_number))
        .where(BeatmapsetSnapshot.beatmapset_id == target.beatmapset_id)
    )

    latest_snapshot = connection.scalar(select_stmt)
    target.snapshot_number = (latest_snapshot or 0) + 1


@event.listens_for(BeatmapsetSnapshot, "after_insert")
def beatmapset_snapshot_after_insert(mapper: Mapper[BeatmapsetSnapshot], connection: Connection, target: BeatmapsetSnapshot):
    """Propagate a new ``BeatmapsetSnapshot`` to dependent tables.

    After insertion:
        - Ensures ``BeatmapsetListing`` references the latest snapshot.
        - Updates all related ``Request`` rows to reference the new snapshot.

    This guarantees that read models and active requests always point to the most recent
    beatmapset state.

    Args:
        mapper:
            SQLAlchemy mapper for ``BeatmapsetSnapshot``.
        connection:
            Active database connection.
        target:
            The newly inserted ``BeatmapsetSnapshot``.

    Side Effects:
        Inserts or updates ``BeatmapsetListing``.
        Bulk-updates ``Request`` rows.
    """
    info = {"id": target.id, "beatmapset_id": target.beatmapset_id}
    logger.debug(f"New BeatmapsetSnapshot detected (after_insert): {info}")

    beatmapset_listing_stmt = (
        select(BeatmapsetListing.id)
        .where(BeatmapsetListing.beatmapset_id == target.beatmapset_id)
    )

    beatmapset_listing_id = connection.scalar(beatmapset_listing_stmt)

    if not beatmapset_listing_id:
        insert_beatmapset_listing_stmt = (
            insert(BeatmapsetListing)
            .values(beatmapset_id=target.beatmapset_id, beatmapset_snapshot_id=target.id)
        )

        connection.execute(insert_beatmapset_listing_stmt)
        logger.debug(f"No existing BeatmapsetListing found, inserted new BeatmapsetListing with beatmapset_snapshot_id={target.id}")
    else:
        update_beatmapset_listing_stmt = (
            update(BeatmapsetListing)
            .where(BeatmapsetListing.id == beatmapset_listing_id)
            .values(beatmapset_snapshot_id=target.id)
        )

        connection.execute(update_beatmapset_listing_stmt)
        logger.debug(f"Updated existing BeatmapsetListing with beatmapset_snapshot_id={target.id}")

    update_request_stmt = (
        update(Request)
        .where(Request.beatmapset_id == target.beatmapset_id)
        .values(beatmapset_snapshot_id=target.id)
    )

    update_request_result = connection.execute(update_request_stmt)
    logger.debug(f"Updated {update_request_result.rowcount} Request(s) with beatmapset_snapshot_id={target.id}")


