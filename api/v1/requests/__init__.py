from connexion import request
from pydantic import ValidationError

from api.utils import prime_query_kwargs, bleach_body
from app.osu_api import OsuAPIClient
from app.database import PostgresqlDB
from app.database.schemas import RequestSchema
from app.security import role_authorization, ownership_authorization
from app.security.overrides import queue_owner_override
from app.database.enums import RoleName
from app.redis import Namespace, ChannelName, RedisClient
from app.redis.models import QueueRequestHandlerTask
from . import tasks

_LOADING_OPTIONS = {
    "beatmapset_snapshot": False,
    "user_profile": False,
    "queue": False
}


@ownership_authorization()
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    requests = await db.get_requests(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    requests_data = [
        RequestSchema.model_validate(request_).model_dump(
            exclude={"beatmapset_snapshot", "user_profile", "queue"}
        )
        for request_ in requests
    ]

    return requests_data, 200


@ownership_authorization()
async def get(request_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    request_ = await db.get_request(
        id=request_id,
        _loading_options=_LOADING_OPTIONS
    )

    if not request_:
        return {"message": f"Request with ID '{request_id}' not found"}, 404

    request_data = RequestSchema.model_validate(request_).model_dump(
        exclude={"beatmapset_snapshot", "user_profile", "queue"}
    )

    return request_data, 200


async def post(body: dict, **kwargs):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    try:
        RequestSchema.model_validate(body)
    except ValidationError as e:
        return {"message": "Invalid input data", "errors": str(e)}, 400

    beatmapset_id = body["beatmapset_id"]
    queue_id = body["queue_id"]
    queue = await db.get_queue(id=queue_id)

    if not queue.is_open:
        return {"message": f"The queue '{queue.name}' is closed"}, 403

    if await db.get_request(beatmapset_id=beatmapset_id, queue_id=queue_id):
        return {"message": f"The request with beatmapset ID '{beatmapset_id}' already exists in queue '{queue.name}'"}, 409

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
        whitelisted_keys=RequestSchema.model_fields.keys(),
        blacklisted_keys={"id", "user_id", "beatmapset_id", "queue_id", "created_at", "updated_at", "beatmapset_snapshot", "user_profile", "queue"}
    )

    request_ = await db.get_request(id=request_id)

    if not request_:
        return {"message": f"Request with ID '{request_id}' not found"}, 404

    delta = {}

    for key, value in body.items():
        if value != getattr(request_, key):
            delta[key] = value

    await db.update_request(request_id, **delta)

    return {"message": "Request updated successfully!"}, 200
