"""Re-exports for the queues v1 API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from connexion.exceptions import Forbidden

from api.decorators import api_query
from api.utils import bleach_body, build_pydantic_include
from app.database.enums import RoleName

if TYPE_CHECKING:
    from starlette.requests import Request

    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.models import ModelClass, Queue
from app.database.queue_access import can_read_queue, queue_visibility_where
from app.database.schemas import QueueSchema
from app.exceptions import Conflict, NotFound
from app.security import role_authorization, with_authenticated_user_id
from app.security.overrides import queue_owner_override
from app.spec import get_include_schema

__all__ = ["get", "patch", "post", "search"]


def _filter_public_rules(queue_data: dict[str, Any]) -> dict[str, Any]:
    """Strip non-public rules from a serialized queue's nested ``rules`` include."""
    rules = queue_data.get("rules")
    if isinstance(rules, list):
        queue_data["rules"] = [rule for rule in rules if rule.get("is_public")]
    return queue_data


@with_authenticated_user_id()
@api_query(ModelClass.QUEUE, many=True)
async def search(
    request: Request, _caller_user_id: int | None = None, **kwargs: Any
) -> APIResponse:
    """Search for queues with visibility filtering.

    Returns:
        Tuple of (queues data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    queues = await db.get_many(
        Queue, _where=await queue_visibility_where(db, _caller_user_id), **kwargs
    )

    if not queues:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=queues[0],
        include_schema=get_include_schema(ModelClass.QUEUE),
        request_include=kwargs.get("_include"),
    )

    queues_data = [
        _filter_public_rules(QueueSchema.model_validate(queue).model_dump(include=include))
        for queue in queues
    ]

    return queues_data, 200, {"Content-Type": "application/json"}


@with_authenticated_user_id()
@api_query(ModelClass.QUEUE)
async def get(
    request: Request, queue_id: int, _caller_user_id: int | None = None, **kwargs: Any
) -> APIResponse:
    """Get a single queue by ID.

    Returns:
        Tuple of (queue data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id, **kwargs)

    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    if not await can_read_queue(db, queue, _caller_user_id):
        # TODO(2026-07-17): this leaks the existence of private queues via 403 vs
        # 404 on NotFound. Migrate to 404 once queue IDs are non-sequential
        # (sequential integer IDs make private queues trivially enumerable even
        # behind a privacy-preserving 404) - see the visibility-enforcement
        # incident from this date for context.
        raise Forbidden("You are not authorized to view this queue")

    include = build_pydantic_include(
        obj=queue,
        include_schema=get_include_schema(ModelClass.QUEUE),
        request_include=kwargs.get("_include"),
    )

    queue_data = _filter_public_rules(QueueSchema.model_validate(queue).model_dump(include=include))

    return queue_data, 200, {"Content-Type": "application/json"}


# @role_authorization(RoleName.ADMIN, override=matching_user_id_override, override_kwargs={"resource_user_id_lookup": "body.user_id"})  # Disable regular users from adding queues for now
@role_authorization(RoleName.ADMIN)
async def post(request: Request, body: dict[str, Any], **_kwargs: Any) -> APIResponse:
    """Create a new queue.

    Returns:
        Tuple of (message, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    queue_name = body["name"]
    user_id = body["user_id"]

    if await db.get(Queue, user_id=user_id, name=queue_name):
        raise Conflict(f"Queue '{queue_name}' already exists for user '{user_id}'")

    body = bleach_body(body, whitelisted_keys={"user_id", "name", "description", "visibility"})

    await db.add(Queue, **body)

    return {"message": "Queue added successfully!"}, 201, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def patch(
    request: Request, queue_id: int, body: dict[str, Any], **_kwargs: Any
) -> APIResponse:
    """Update an existing queue.

    Returns:
        Tuple of (message, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    body = bleach_body(body, whitelisted_keys={"name", "description", "visibility", "is_open"})

    queue = await db.get(Queue, id=queue_id)

    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    delta = {key: value for key, value in body.items() if value != getattr(queue, key)}

    if delta:
        await db.update(Queue, queue_id, **delta)

    return {"message": "Queue updated successfully!"}, 200, {"Content-Type": "application/json"}
