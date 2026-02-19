from app.database import PostgresqlDB
from app.database.models import Queue, Request
from app.utils import get_nested_value


async def matching_user_id_override(
    authenticated_user_id_lookup: str = "user",
    resource_user_id_lookup: str = "user_id", **kwargs
) -> bool:
    """Override authorization when authenticated and resource user IDs match.

    Extracts both IDs from provided keyword arguments and returns ``True`` if they are
    equal and non-null.

    Returns:
        ``True`` if user IDs match; otherwise ``False``.
    """
    authenticated_user_id = get_nested_value(kwargs, authenticated_user_id_lookup)
    resource_user_id = get_nested_value(kwargs, resource_user_id_lookup)

    return (
        authenticated_user_id == resource_user_id
        and authenticated_user_id is not None
        and resource_user_id is not None
    )


async def queue_owner_override(
    db: PostgresqlDB,
    authenticated_user_id_lookup: str = "user",
    from_request: bool = False, **kwargs
) -> bool:
    """Override authorization if the authenticated user owns the queue.

    Resolves queue ownership either directly from ``queue_id`` or indirectly through a
    ``request_id``.

    Args:
        db:
            Active database interface.
        authenticated_user_id_lookup:
            Key/path for authenticated user ID.
        from_request:
            Whether ownership should be resolved via Request -> Queue.

    Returns:
        ``True`` if the authenticated user owns the queue; otherwise ``False``.
    """
    authenticated_user_id = get_nested_value(kwargs, authenticated_user_id_lookup)

    if not from_request:
        queue = await db.get(Queue, id=kwargs["queue_id"])
    else:
        queue = (await db.get(Request, id=kwargs["request_id"], _include={"queue": True})).queue

    return authenticated_user_id == queue.user_id
