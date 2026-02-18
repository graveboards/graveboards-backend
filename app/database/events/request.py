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
    """Bind a ``Request`` to the latest ``BeatmapsetSnapshot``.

    Ensures referential consistency by resolving and attaching the most recent snapshot
    ID for the associated beatmapset at the time of request creation.

    Args:
        mapper:
            SQLAlchemy mapper for ``Request``.
        connection:
            Active database connection.
        target:
            The ``Request`` being inserted.

    Raises:
        ValueError:
            If no ``BeatmapsetSnapshot`` exists for the beatmapset.

    Side Effects:
        Mutates ``target.beatmapset_snapshot_id``.
    """
    latest_beatmapset_snapshot_id_stmt = (
        select(func.max(BeatmapsetSnapshot.id))
        .where(BeatmapsetSnapshot.beatmapset_id == target.beatmapset_id)
    )

    latest_beatmapset_snapshot_id = connection.scalar(latest_beatmapset_snapshot_id_stmt)

    if latest_beatmapset_snapshot_id is None:
        raise ValueError(f"No BeatmapsetSnapshot found for beatmapset ID {target.beatmapset_id}")

    target.beatmapset_snapshot_id = latest_beatmapset_snapshot_id
