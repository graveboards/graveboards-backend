from connexion import request

from api.utils import build_pydantic_include
from app.exceptions import NotFound
from app.security import role_authorization
from app.database.enums import RoleName
from app.redis import Namespace
from app.redis.models import QueueRequestHandlerTask
from app.spec import get_include_schema


@role_authorization(RoleName.ADMIN)
async def search(**kwargs):
    rc = request.state.rc

    limit = kwargs.get("limit")
    offset = kwargs.get("offset")

    task_hash_names = await rc.paginate_scan(f"{Namespace.QUEUE_REQUEST_HANDLER_TASK.value}:*", type_="HASH", limit=limit, offset=offset)

    if not task_hash_names:
        return [], 200, {"Content-Type": "application/json"}

    serialized_tasks = [await rc.hgetall(task_hash_name) for task_hash_name in task_hash_names]
    deserialized_tasks = [QueueRequestHandlerTask.deserialize(serialized_task) for serialized_task in serialized_tasks]

    include = build_pydantic_include(
        obj=deserialized_tasks[0],
        include_schema=get_include_schema(schema_name="RequestTaskInclude"),
        request_include=kwargs.get("include")
    )

    tasks = [deserialized_task.model_dump(mode="json", include=include) for deserialized_task in deserialized_tasks]

    return tasks, 200, {"Content-Type": "application/json"}


async def get(hashed_id: int, **kwargs):
    rc = request.state.rc

    task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(hashed_id)
    serialized_task = await rc.hgetall(task_hash_name)

    if not serialized_task:
        raise NotFound(f"Request task with hashed ID '{hashed_id}' not found")

    deserialized_task = QueueRequestHandlerTask.deserialize(serialized_task)

    include = build_pydantic_include(
        obj=deserialized_task,
        include_schema=get_include_schema(schema_name="RequestTaskInclude"),
        request_include=kwargs.get("include")
    )

    task = deserialized_task.model_dump(mode="json", include=include)

    return task, 200, {"Content-Type": "application/json"}
