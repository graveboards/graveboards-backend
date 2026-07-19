from connexion import request

from app.database import PostgresqlDB
from app.database.models import Queue
from app.database.queue_access import is_queue_owner_or_manager, can_read_queue
from app.database.schemas import RuleSchema, RuleCreateSchema, RuleReplaceSchema, RuleUpdateSchema
from app.exceptions import NotFound, Conflict, BadRequest
from app.security import role_authorization, with_authenticated_user_id
from app.security.overrides import queue_owner_override
from app.database.enums import RoleName
from app.database.crud.rules import RuleCRUD

__all__ = ["search", "get", "post", "patch", "delete", "put"]


async def _can_view_private_rules(db: PostgresqlDB, queue_id: int, caller_user_id: int | None) -> bool:
    return await is_queue_owner_or_manager(db, queue_id, caller_user_id)


@with_authenticated_user_id()
async def search(queue_id: int, _caller_user_id: int = None, **kwargs):
    """GET /queues/{queue_id}/rules — list all rules for a queue."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue or not await can_read_queue(db, queue, _caller_user_id):
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        rules = await crud.get_rules(queue_id, session=session)

    if not await _can_view_private_rules(db, queue_id, _caller_user_id):
        rules = [r for r in rules if r.is_public]

    return [RuleSchema.model_validate(r).model_dump() for r in rules], 200, {"Content-Type": "application/json"}


@with_authenticated_user_id()
async def get(queue_id: int, rule_id: int, _caller_user_id: int = None, **kwargs):
    """GET /queues/{queue_id}/rules/{rule_id} — get a single rule."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue or not await can_read_queue(db, queue, _caller_user_id):
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        rule = await crud.get_rule(queue_id, rule_id, session=session)

    if not rule or (not rule.is_public and not await _can_view_private_rules(db, queue_id, _caller_user_id)):
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return RuleSchema.model_validate(rule).model_dump(), 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def post(queue_id: int, body: dict, **kwargs):
    """POST /queues/{queue_id}/rules — add a single rule to a queue."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    try:
        rule_data = RuleCreateSchema.model_validate(body).model_dump(exclude_none=True)
    except Exception as e:
        raise BadRequest(f"Invalid rule data: {e}")

    crud = RuleCRUD()
    async with db.session() as session:
        created = await crud.create_rule(queue_id, rule_data, session=session)

    return RuleSchema.model_validate(created).model_dump(), 201, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def patch(queue_id: int, rule_id: int, body: dict, **kwargs):
    """PATCH /queues/{queue_id}/rules/{rule_id} — update a single rule."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    try:
        updates = RuleUpdateSchema.model_validate(body).model_dump(exclude_unset=True)
    except Exception as e:
        raise BadRequest(f"Invalid rule update: {e}")

    crud = RuleCRUD()
    async with db.session() as session:
        updated = await crud.update_rule(rule_id, queue_id, updates, session=session)

    if not updated:
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return RuleSchema.model_validate(updated).model_dump(), 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def delete(queue_id: int, rule_id: int, **kwargs):
    """DELETE /queues/{queue_id}/rules/{rule_id} — remove a single rule."""
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
async def put(queue_id: int, body: dict, **kwargs):
    """PUT /queues/{queue_id}/rules — replace all rules for a queue."""
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
            raise BadRequest(f"Invalid rule data: {e}")

    crud = RuleCRUD()
    async with db.session() as session:
        created = await crud.upsert_rules(queue_id, validated, session=session)

    return [RuleSchema.model_validate(r).model_dump() for r in created], 200, {"Content-Type": "application/json"}
