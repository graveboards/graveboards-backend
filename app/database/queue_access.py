from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.sql import or_
from sqlalchemy.sql.elements import ColumnElement

from app.database.models import Queue, User

if TYPE_CHECKING:
    from app.database import PostgresqlDB


def queue_visibility_where(caller_user_id: int | None) -> ColumnElement:
    """Build a WHERE condition restricting queues to what a caller may see in a listing.

    Queue.visibility: 0 = public (everyone), 1 = unlisted (excluded from listings/
    search, but directly fetchable by ID), 2 = private (owner/managers only,
    everywhere). A caller always sees their own owned or managed queues regardless
    of visibility, since listings double as "my queues" views.
    """
    if caller_user_id is None:
        return Queue.visibility == 0

    return or_(
        Queue.visibility == 0,
        Queue.user_id == caller_user_id,
        Queue.managers.any(User.id == caller_user_id),
    )


async def is_queue_owner_or_manager(
    db: "PostgresqlDB",
    queue_id: int,
    caller_user_id: int | None,
) -> bool:
    """Check whether ``caller_user_id`` owns or manages the given queue."""
    if caller_user_id is None:
        return False

    match = await db.get(
        Queue,
        id=queue_id,
        _where=or_(Queue.user_id == caller_user_id, Queue.managers.any(User.id == caller_user_id)),
    )

    return match is not None
