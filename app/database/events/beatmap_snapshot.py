from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select, func, insert, update
from sqlalchemy.orm.mapper import Mapper

from app.logging import get_logger
from app.database.models import BeatmapSnapshot, BeatmapListing

__all__ = [
    "beatmap_snapshot_before_insert",
    "beatmap_snapshot_after_insert"
]

logger = get_logger(__name__)


@event.listens_for(BeatmapSnapshot, "before_insert")
def beatmap_snapshot_before_insert(mapper: Mapper[BeatmapSnapshot], connection: Connection, target: BeatmapSnapshot):
    """Assign the next sequential snapshot number for a ``BeatmapSnapshot``.

    Before insertion, this listener determines the current maximum ``snapshot_number``
    for the ``beatmap_id`` and increments it to ensure per-beatmap version ordering.

    Args:
        mapper:
            SQLAlchemy mapper for ``BeatmapSnapshot``.
        connection:
            Active database connection for executing SQL.
        target:
            The ``BeatmapSnapshot`` instance being inserted.

    Raises:
        SQLAlchemyError:
            If the aggregate query fails.

    Side Effects:
        Mutates ``target.snapshot_number`` prior to persistence.
    """
    select_stmt = (
        select(func.max(BeatmapSnapshot.snapshot_number))
        .where(BeatmapSnapshot.beatmap_id == target.beatmap_id)
    )

    latest_snapshot = connection.scalar(select_stmt)
    target.snapshot_number = (latest_snapshot or 0) + 1


@event.listens_for(BeatmapSnapshot, "after_insert")
def beatmap_snapshot_after_insert(mapper: Mapper[BeatmapSnapshot], connection: Connection, target: BeatmapSnapshot):
    """Synchronize ``BeatmapListing`` to the newly inserted snapshot.

    Ensures that each beatmap has a corresponding ``BeatmapListing`` row pointing to its
    latest snapshot. If no listing exists, one is created; otherwise, it is updated to
    reference the new snapshot.

    Args:
        mapper:
            SQLAlchemy mapper for ``BeatmapSnapshot``.
        connection:
            Active database connection.
        target:
            The newly inserted ``BeatmapSnapshot``.

    Raises:
        SQLAlchemyError: If insert/update statements fail.

    Side Effects:
        Inserts or updates ``BeatmapListing``.
    """
    info = {"id": target.id, "beatmap_id": target.beatmap_id}
    logger.debug(f"New BeatmapSnapshot detected (after_insert): {info}")
    
    beatmap_listing_stmt = (
        select(BeatmapListing.id)
        .where(BeatmapListing.beatmap_id == target.beatmap_id)
    )

    beatmap_listing_id = connection.scalar(beatmap_listing_stmt)

    if not beatmap_listing_id:
        insert_beatmap_listing_stmt = (
            insert(BeatmapListing)
            .values(beatmap_id=target.beatmap_id, beatmap_snapshot_id=target.id)
        )

        connection.execute(insert_beatmap_listing_stmt)
        logger.debug(f"No existing BeatmapListing found, inserted new BeatmapListing with beatmap_snapshot_id={target.id}")
    else:
        update_beatmap_listing_stmt = (
            update(BeatmapListing)
            .where(BeatmapListing.id == beatmap_listing_id)
            .values(beatmap_snapshot_id=target.id)
        )

        connection.execute(update_beatmap_listing_stmt)
        logger.debug(f"Updated existing BeatmapListing with beatmap_snapshot_id={target.id}")
