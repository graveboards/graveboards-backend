from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import insert
from sqlalchemy.orm.mapper import Mapper

from app.database.models import Queue, QueueListing

__all__ = [
    "queue_after_insert"
]


@event.listens_for(Queue, "after_insert")
def queue_after_insert(mapper: Mapper[Queue], connection: Connection, target: Queue):
    stmt = (
        insert(QueueListing)
        .values(queue_id=target.id)
    )

    connection.execute(stmt)
