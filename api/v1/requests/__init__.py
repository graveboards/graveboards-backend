from connexion import request
from connexion.exceptions import Forbidden
from structlog.contextvars import get_contextvars

from app.logging import get_logger
from api.decorators import api_query
from api.utils import bleach_body, build_pydantic_include
from app.exceptions import NotFound, Conflict, BadRequest
from app.osu_api import OsuAPIClient
from app.database import PostgresqlDB
from app.database.models import Request, Queue, ModelClass
from app.database.schemas import RequestSchema
from app.security import role_authorization, ownership_authorization
from app.security.overrides import queue_owner_override
from app.database.enums import RoleName
from app.redis import Namespace, ChannelName, RedisClient
from app.redis.models import QueueRequestHandlerTask, QueueRequestValidationTask
from app.spec import get_include_schema
from app.database.rules.context import ExecutionContext
from app.database.rules.engine.phase1_runner import Phase1Runner
from app.database.rules.exceptions import RuleViolationError
from app.database.rules.validators.metadata import (
    SongIdentityProvider,
    BeatmapStatsProvider,
    CreatorIdentityProvider,
    DurationProvider,
)
from . import tasks

_METADATA_PROVIDERS = {
    "song_identity": SongIdentityProvider,
    "beatmap_stats": BeatmapStatsProvider,
    "creator_identity": CreatorIdentityProvider,
    "duration": DurationProvider,
}

logger = get_logger(__name__)


@ownership_authorization()
@api_query(ModelClass.REQUEST, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    requests = await db.get_many(Request, **kwargs)

    if not requests:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=requests[0],
        include_schema=get_include_schema(ModelClass.REQUEST),
        request_include=kwargs.get("_include"),
    )

    requests_data = [
        RequestSchema.model_validate(request_).model_dump(include=include) for request_ in requests
    ]

    return requests_data, 200, {"Content-Type": "application/json"}


@ownership_authorization()
@api_query(ModelClass.REQUEST)
async def get(request_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    request_ = await db.get(Request, id=request_id, **kwargs)

    if not request_:
        raise NotFound(f"Request with ID '{request_id}' not found")

    include = build_pydantic_include(
        obj=request,
        include_schema=get_include_schema(ModelClass.REQUEST),
        request_include=kwargs.get("_include"),
    )

    request_data = RequestSchema.model_validate(request_).model_dump(include=include)

    return request_data, 200, {"Content-Type": "application/json"}


async def post(body: dict, **kwargs):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    beatmapset_id = body["beatmapset_id"]
    queue_id = body["queue_id"]
    user_id = body["user_id"]
    queue = await db.get(Queue, id=queue_id)

    if not queue:
        raise NotFound(f"The queue with ID '{queue_id}' not found")

    if not queue.is_open:
        raise Forbidden(f"The queue '{queue.name}' is closed")

    if await db.get(Request, beatmapset_id=beatmapset_id, queue_id=queue_id):
        raise Conflict(
            f"The request with beatmapset ID '{beatmapset_id}' already exists in queue '{queue.name}'"
        )

    async with OsuAPIClient(rc) as oac:
        beatmapset_dict = await oac.get_beatmapset(beatmapset_id)

    if (status := beatmapset_dict["status"]) in {"ranked", "approved", "qualified", "loved"}:
        raise BadRequest(f"The beatmapset is already {status} on osu!")

    await _check_queue_rules_phase1(
        queue_id=queue_id,
        user_id=user_id,
        beatmapset=beatmapset_dict,
        db=db,
        rc=rc,
    )

    ctx = get_contextvars()
    task = QueueRequestHandlerTask(**body, http_request_id=ctx.get("request_id", ""))
    task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(task.hashed_id)

    logger.debug(
        f"POST /requests: creating handler task hashed_id={task.hashed_id}, "
        f"hash_name={task_hash_name}, queue_id={queue_id}, beatmapset_id={beatmapset_id}"
    )

    if await rc.exists(task_hash_name):
        serialized_existing_task = await rc.hgetall(task_hash_name)
        existing_task = QueueRequestHandlerTask.deserialize(serialized_existing_task)
        logger.debug(
            f"POST /requests: task already exists at {task_hash_name}, "
            f"keys={list(serialized_existing_task.keys())}, "
            f"failed_at={existing_task.failed_at}"
        )

        if existing_task.failed_at:
            logger.debug(f"POST /requests: deleting existing failed task at {task_hash_name}")
            await rc.delete(task_hash_name)
        else:
            raise Conflict(
                f"The request with beatmapset ID '{beatmapset_id}' in queue '{queue.name}' is currently being processed"
            )

    await rc.hset(task_hash_name, mapping=task.serialize())
    logger.debug(f"POST /requests: stored task at {task_hash_name}, publishing to {ChannelName.QUEUE_REQUEST_HANDLER_TASKS.value}")
    await rc.publish(ChannelName.QUEUE_REQUEST_HANDLER_TASKS.value, task.hashed_id)
    logger.debug(f"POST /requests: published job_id={task.hashed_id}")

    return (
        {"message": "Request submitted and queued for processing!", "task_id": task.hashed_id},
        202,
        {"Content-Type": "application/json"},
    )


async def _check_queue_rules_phase1(
    queue_id: int,
    user_id: int,
    beatmapset: dict,
    db: PostgresqlDB,
    rc: RedisClient,
) -> None:
    from app.database.crud.rules import RuleCRUD

    rule_crud = RuleCRUD()
    async with db.session() as session:
        rules = await rule_crud.get_rules(queue_id, only_active=True, session=session)

    context = ExecutionContext(
        queue_id=queue_id,
        user_id=user_id,
        beatmapset=beatmapset,
        db=db,
        redis=rc,
        metadata_providers=_METADATA_PROVIDERS,
    )

    runner = Phase1Runner()
    await runner.run(rules, context)


@role_authorization(
    RoleName.ADMIN, override=queue_owner_override, override_kwargs={"from_request": True}
)
async def patch(request_id: int, body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    body = bleach_body(body, whitelisted_keys={"status"})

    request_ = await db.get(Request, id=request_id)

    if not request_:
        raise NotFound(f"Request with ID '{request_id}' not found")

    delta = {}

    for key, value in body.items():
        if value != getattr(request_, key):
            delta[key] = value

    await db.update(Request, request_id, **delta)

    return {"message": "Request updated successfully!"}, 200, {"Content-Type": "application/json"}


@role_authorization(
    RoleName.ADMIN, override=queue_owner_override, override_kwargs={"from_request": True}
)
async def delete(request_id: int, **kwargs):
    db: PostgresqlDB = request.state.db
    rc: RedisClient = request.state.rc

    request_ = await db.get(Request, id=request_id)

    if not request_:
        raise NotFound(f"Request with ID '{request_id}' not found")

    handler_task_hash = hash((request_.queue_id, request_.beatmapset_id)) & 0x7FFFFFFFFFFFFFFF
    handler_task_key = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(handler_task_hash)
    logger.debug(
        f"DELETE /requests/{request_id}: cleaning up handler_task_hash={handler_task_hash}, "
        f"handler_task_key={handler_task_key}, validation_task_hash={hash(('validation', request_.id)) & 0x7FFFFFFFFFFFFFFF}"
    )
    await rc.delete(handler_task_key)

    validation_task_hash = hash(("validation", request_.id)) & 0x7FFFFFFFFFFFFFFF
    validation_task_key = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(validation_task_hash)
    await rc.delete(validation_task_key)

    await db.delete(Request, id=request_id)
    logger.debug(f"DELETE /requests/{request_id}: request deleted from DB")

    return {"message": "Request deleted successfully!"}, 200, {"Content-Type": "application/json"}
