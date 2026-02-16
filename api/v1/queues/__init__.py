from connexion import request

from api.decorators import api_query
from api.utils import bleach_body, build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import Queue, ModelClass
from app.database.schemas import QueueSchema
from app.exceptions import NotFound, Conflict
from app.security import role_authorization
from app.security.overrides import queue_owner_override
from app.database.enums import RoleName
from app.spec import get_include_schema


@api_query(ModelClass.QUEUE, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    queues = await db.get_many(
        Queue,
        **kwargs
    )

    if not queues:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=queues[0],
        include_schema=get_include_schema(ModelClass.QUEUE),
        request_include=kwargs.get("_include")
    )

    queues_data = [
        QueueSchema.model_validate(queue).model_dump(include=include)
        for queue in queues
    ]

    return queues_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.QUEUE)
async def get(queue_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    queue = await db.get(
        Queue,
        id=queue_id,
        **kwargs
    )

    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    include = build_pydantic_include(
        obj=queue,
        include_schema=get_include_schema(ModelClass.QUEUE),
        request_include=kwargs.get("_include")
    )

    queue_data = QueueSchema.model_validate(queue).model_dump(include=include)

    return queue_data, 200, {"Content-Type": "application/json"}


# @role_authorization(RoleName.ADMIN, override=matching_user_id_override, override_kwargs={"resource_user_id_lookup": "body.user_id"})  # Disable regular users from adding queues for now
@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    if await db.get(Queue, user_id=body["user_id"], name=body["name"]):
        raise Conflict(f"The queue with name '{body["name"]}' for user with ID '{body["user_id"]}' already exists")

    body = bleach_body(
        body,
        whitelisted_keys={"user_id", "name", "description", "visibility"}
    )

    await db.add(Queue, **body)

    return {"message": "Queue added successfully!"}, 201, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def patch(queue_id: int, body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    body = bleach_body(
        body,
        whitelisted_keys={"name", "description", "visibility", "is_open"}
    )

    queue = await db.get(Queue, id=queue_id)

    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    delta = {}

    for key, value in body.items():
        if value != getattr(queue, key):
            delta[key] = value

    await db.update(Queue, queue_id, **delta)

    return {"message": "Queue updated successfully!"}, 200, {"Content-Type": "application/json"}
