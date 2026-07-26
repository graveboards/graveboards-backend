from connexion import request
from starlette.requests import Request
from typing import Any
from starlette.responses import Response

from app.database import PostgresqlDB
from app.database.crud.rules import RuleCRUD
from app.database.enums import RoleName
from app.database.models import Queue
from app.database.queue_access import can_read_queue, is_queue_owner_or_manager
from app.database.schemas import RuleCreateSchema, RuleReplaceSchema, RuleSchema, RuleUpdateSchema
from app.exceptions import BadRequest, NotFound
from app.security import role_authorization, with_authenticated_user_id
from app.security.overrides import queue_owner_override

__all__ = ["search", "get", "post", "patch", "delete", "put"]


async def _can_view_private_rules(
    db: PostgresqlDB, queue_id: int, caller_user_id: int | None
) -> bool:
    return await is_queue_owner_or_manager(db, queue_id, caller_user_id)


@with_authenticated_user_id()
async def search(request: Request, queue_id: int, _caller_user_id: int | None = None, **kwargs: Any) -> Response:
    """List all rules for a queue.

    Args:
        queue_id: The ID of the queue.
        _caller_user_id: The authenticated user ID.

    Returns:
        Tuple of (rules list, status code, headers).

    Raises:
        NotFound: If the queue doesn't exist or isn't readable.
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue or not await can_read_queue(db, queue, _caller_user_id):
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        rules = await crud.get_rules(queue_id, session=session)

    if not await _can_view_private_rules(db, queue_id, _caller_user_id):
        rules = [r for r in rules if r.is_public]

    return (
        [RuleSchema.model_validate(r).model_dump() for r in rules],
        200,
        {"Content-Type": "application/json"},
    )


@with_authenticated_user_id()
async def get(request: Request, queue_id: int, rule_id: int, _caller_user_id: int | None = None, **kwargs: Any) -> Response:
    """Get a single rule by ID.

    Args:
        queue_id: The ID of the queue.
        rule_id: The ID of the rule.
        _caller_user_id: The authenticated user ID.

    Returns:
        Tuple of (rule dict, status code, headers).

    Raises:
        NotFound: If the queue or rule doesn't exist.
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue or not await can_read_queue(db, queue, _caller_user_id):
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        rule = await crud.get_rule(queue_id, rule_id, session=session)

    if not rule or (
        not rule.is_public and not await _can_view_private_rules(db, queue_id, _caller_user_id)
    ):
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return RuleSchema.model_validate(rule).model_dump(), 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def post(request: Request, queue_id: int, body: dict, **kwargs: Any) -> Response:
    """Add a single rule to a queue.

    Args:
        queue_id: The ID of the queue.
        body: The rule data to create.

    Returns:
        Tuple of (created rule dict, status code, headers).

    Raises:
        NotFound: If the queue doesn't exist.
        BadRequest: If the rule data is invalid.
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    try:
        rule_data = RuleCreateSchema.model_validate(body).model_dump(exclude_none=True)
    except Exception as e:
        raise BadRequest(f"Invalid rule data: {e}") from e

    crud = RuleCRUD()
    async with db.session() as session:
        created = await crud.create_rule(queue_id, rule_data, session=session)

    return (
        RuleSchema.model_validate(created).model_dump(),
        201,
        {"Content-Type": "application/json"},
    )


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def patch(request: Request, queue_id: int, rule_id: int, body: dict, **kwargs: Any) -> Response:
    """Update a single rule.

    Args:
        queue_id: The ID of the queue.
        rule_id: The ID of the rule.
        body: The rule updates.

    Returns:
        Tuple of (updated rule dict, status code, headers).

    Raises:
        NotFound: If the queue or rule doesn't exist.
        BadRequest: If the rule update data is invalid.
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    try:
        updates = RuleUpdateSchema.model_validate(body).model_dump(exclude_unset=True)
    except Exception as e:
        raise BadRequest(f"Invalid rule update: {e}") from e

    crud = RuleCRUD()
    async with db.session() as session:
        updated = await crud.update_rule(rule_id, queue_id, updates, session=session)

    if not updated:
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return (
        RuleSchema.model_validate(updated).model_dump(),
        200,
        {"Content-Type": "application/json"},
    )


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def delete(request: Request, queue_id: int, rule_id: int, **kwargs: Any) -> Response:
    """Remove a single rule from a queue.

    Args:
        queue_id: The ID of the queue.
        rule_id: The ID of the rule.

    Returns:
        Tuple of (message dict, status code, headers).

    Raises:
        NotFound: If the queue or rule doesn't exist.
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        deleted = await crud.delete_rule(rule_id, queue_id, session=session)

    if not deleted:
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return {"message": "Rule deleted successfully!"}, 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def put(request: Request, queue_id: int, body: dict, **kwargs: Any) -> Response:
    """Replace all rules for a queue.

    Args:
        queue_id: The ID of the queue.
        body: The new rules data (must include a 'rules' array).

    Returns:
        Tuple of (message dict, status code, headers).

    Raises:
        NotFound: If the queue doesn't exist.
        BadRequest: If the body doesn't include a 'rules' array or data is invalid.
    """
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    if "rules" not in body or not isinstance(body["rules"], list):
        raise BadRequest("Request body must include a 'rules' array")

    rules_data = body["rules"]

    validated = []
    for data in rules_data:
        try:
            validated.append(RuleReplaceSchema.model_validate(data).model_dump(exclude_none=True))
        except Exception as e:
            raise BadRequest(f"Invalid rule data: {e}") from e

    crud = RuleCRUD()
    async with db.session() as session:
        created = await crud.upsert_rules(queue_id, validated, session=session)

    return (
        [RuleSchema.model_validate(r).model_dump() for r in created],
        200,
        {"Content-Type": "application/json"},
    )
