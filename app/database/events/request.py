from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import select, insert
from sqlalchemy.orm.mapper import Mapper

from app.database.models import Request, RequestListing, BeatmapsetListing, QueueListing

__all__ = [
    "request_after_insert"
]


@event.listens_for(Request, "after_insert")
def request_after_insert(mapper: Mapper[Request], connection: Connection, target: Request):
    beatmapset_listing_id_select_stmt = (
        select(BeatmapsetListing.id)
        .where(BeatmapsetListing.beatmapset_id == target.beatmapset_id)
    )
    queue_listing_id_select_stmt = (
        select(QueueListing.id)
        .where(QueueListing.queue_id == target.queue_id)
    )

    beatmapset_listing_id = connection.scalar(beatmapset_listing_id_select_stmt)
    queue_listing_id = connection.scalar(queue_listing_id_select_stmt)

    if not beatmapset_listing_id:
        raise RuntimeError(f"BeatmapsetListing doesn't exist for beatmapset with id {target.beatmapset_id}")

    if not queue_listing_id:
        raise RuntimeError(f"QueueListing doesn't exist for queue with id {target.queue_id}")

    stmt = (
        insert(RequestListing)
        .values(
            request_id=target.id,
            beatmapset_listing_id=beatmapset_listing_id,
            queue_listing_id=queue_listing_id
        )
    )

    connection.execute(stmt)
