from app.database import PostgresqlDB
from app.utils import get_nested_value


async def matching_user_id_override(authenticated_user_id_lookup: str = "user", resource_user_id_lookup: str = "user_id", **kwargs) -> bool:
    authenticated_user_id = get_nested_value(kwargs, authenticated_user_id_lookup)
    resource_user_id = get_nested_value(kwargs, resource_user_id_lookup)

    return authenticated_user_id == resource_user_id


async def queue_owner_override(_db: PostgresqlDB, authenticated_user_id_lookup: str = "user", from_request: bool = False, **kwargs) -> bool:
    authenticated_user_id = get_nested_value(kwargs, authenticated_user_id_lookup)

    if not from_request:
        queue = await _db.get_queue(id=kwargs["queue_id"])
    else:
        queue = (await _db.get_request(id=kwargs["request_id"], _loading_options={"queue": True})).queue

    return authenticated_user_id == queue.user_id
