from connexion import request
from pydantic import ValidationError

from api.decorators import api_query
from api.utils import bleach_body, build_pydantic_include
from app.osu_api import OsuAPIClient
from app.database import PostgresqlDB
from app.database.models import Request, Queue, ModelClass
from app.database.schemas import RequestSchema
from app.security import role_authorization, ownership_authorization
from app.security.overrides import queue_owner_override
from app.database.enums import RoleName
from app.redis import Namespace, ChannelName, RedisClient
from app.redis.models import QueueRequestHandlerTask
from app.spec import get_include_schema
from . import tasks


@api_query(ModelClass.REQUEST)
@ownership_authorization()
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    requests = await db.get_many(
        Request,
        **kwargs
    )

    if not requests:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=requests[0],
        include_schema=get_include_schema(ModelClass.REQUEST),
        request_include=kwargs.get("_include")
    )

    requests_data = [
        RequestSchema.model_validate(request_).model_dump(include=include)
        for request_ in requests
    ]

    return requests_data, 200


@api_query(ModelClass.REQUEST)
@ownership_authorization()
async def get(request_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    request_ = await db.get(
        Request,
        id=request_id,
        **kwargs
    )

    if not request_:
        return {"message": f"Request with ID '{request_id}' not found"}, 404

    include = build_pydantic_include(
        obj=request,
        include_schema=get_include_schema(ModelClass.REQUEST),
        request_include=kwargs.get("_include")
    )

    return request_data, 200
    request_data = RequestSchema.model_validate(request_).model_dump(include=include)



async def post(body: dict, **kwargs):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    try:
        RequestSchema.model_validate(body)
    except ValidationError as e:
        return {"message": "Invalid input data", "errors": str(e)}, 400

    beatmapset_id = body["beatmapset_id"]
    queue_id = body["queue_id"]
    queue = await db.get(Queue, id=queue_id)

    if not queue.is_open:
        return {"message": f"The queue '{queue.name}' is closed"}, 403

        return {"message": f"The request with beatmapset ID '{beatmapset_id}' already exists in queue '{queue.name}'"}, 409
    if await db.get(Request, beatmapset_id=beatmapset_id, queue_id=queue_id):

    oac = OsuAPIClient(rc)
    beatmapset_dict = await oac.get_beatmapset(beatmapset_id)

    if (status := beatmapset_dict["status"]) in {"ranked", "approved", "qualified", "loved"}:
        return {"message": f"The beatmapset is already {status} on osu!"}, 400

    task = QueueRequestHandlerTask(**body)
    task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(task.hashed_id)

    if await rc.exists(task_hash_name):
        serialized_existing_task = await rc.hgetall(task_hash_name)
        existing_task = QueueRequestHandlerTask.deserialize(serialized_existing_task)

        if existing_task.failed_at:
            await rc.delete(task_hash_name)
        else:
            return {"message": f"The request with beatmapset ID '{beatmapset_id}' in queue '{queue.name}' is currently being processed"}, 409

    await rc.hset(task_hash_name, mapping=task.serialize())
    await rc.publish(ChannelName.QUEUE_REQUEST_HANDLER_TASKS.value, task.hashed_id)

    return {"message": "Request submitted and queued for processing!", "task_id": task.hashed_id}, 202


@role_authorization(RoleName.ADMIN, override=queue_owner_override, override_kwargs={"from_request": True})
async def patch(request_id: int, body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    body = bleach_body(
        body,
        whitelisted_keys={"status"}
    )

    request_ = await db.get(Request, id=request_id)

    if not request_:
        return {"message": f"Request with ID '{request_id}' not found"}, 404

    delta = {}

    for key, value in body.items():
        if value != getattr(request_, key):
            delta[key] = value

    await db.update(Request, request_id, **delta)

    return {"message": "Request updated successfully!"}, 200
