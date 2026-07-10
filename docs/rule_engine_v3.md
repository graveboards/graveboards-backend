# Rule Engine v3 — Implementation Plan

## Overview

Move the rule engine from a hidden `restrictions` key inside `PATCH /queues/{id}` into a dedicated, fully-featured REST resource at `POST /queues/{queue_id}/rules` with full CRUD. Rename all "restriction" terminology to "rule" throughout the codebase.

**Key decisions:**
- No backwards compatibility — nothing has been deployed yet.
- Full rename: `restriction` → `rule` (including DB column `restriction_type` → `type`).
- New endpoint: `/api/v1/queues/{queue_id}/rules` with sub-resource `/api/v1/queues/{queue_id}/rules/{rule_id}`.

## Git Workflow

- Use the new branch `rule-engine` for all commits throughout the plan
- After implementing each phase, commit with descriptive single-line messages.
- Do NOT use multi-line commit messages, `--amend`, or squash commits during implementation.
- Do not push anything to origin under any circumstances.

---

## Phase 1 — Foundation: Rename & Restructure

Rename all "restriction" terminology to "rule" across the codebase. No new functionality — just find-and-replace with verification.

### Files to rename

| Old Path | New Path |
|---|---|
| `app/database/models/queue_restriction.py` | `app/database/models/queue_rule.py` |
| `app/database/schemas/restriction.py` | `app/database/schemas/rule.py` |
| `app/database/crud/restrictions.py` | `app/database/crud/rules.py` |
| `app/database/restrictions/` (directory) | `app/database/rules/` (directory) |
| `app/database/restrictions/` sub-files | `app/database/rules/` sub-files |
| `api/v1/spec/schemas/restriction.yaml` | `api/v1/spec/schemas/rule.yaml` |
| `tests/integration/api/test_restrictions.py` | `tests/integration/api/test_rules.py` |
| `tests/unit/restrictions/test_rule_validation_service.py` | `tests/unit/rules/test_rule_validation_service.py` |

### Rename map (find-and-replace)

**Python identifiers:**

| Old | New |
|---|---|
| `QueueRestriction` | `QueueRule` |
| `RestrictionSchema` | `RuleSchema` |
| `RestrictionCreateSchema` | `RuleCreateSchema` |
| `RestrictionUpdateSchema` | `RuleUpdateSchema` |
| `RestrictionType` | `RuleType` |
| `RestrictionScope` | `RuleScope` |
| `RestrictionViolationError` | `RuleViolationError` |
| `RestrictionCRUD` | `RuleCRUD` |
| `RESTRICTION_REGISTRY` | `RULE_REGISTRY` |
| `RESTRICTION_TIERS` | `RULE_TIERS` |
| `get_validator` | `get_validator` (keep — still valid) |
| `register_validator` | `register_validator` (keep) |
| `get_validators_for_tier` | `get_validators_for_tier` (keep) |
| `get_supported_versions` | `get_supported_versions` (keep) |
| `restriction_type` (Python variable/attribute) | `type` |
| `upsert_restrictions` | `upsert_rules` |
| `get_restrictions` | `get_rules` |
| `update_restriction` | `update_rule` |
| `_delete_all_for_queue` | `_delete_all_for_queue` (keep — internal, but rename to `_delete_all_for_rule` for consistency) |
| `restrictions` (QueueSchema field, QueueUpdateSchema field) | `rules` |
| `queue.restrictions` (relationship) | `queue.rules` |
| `back_populates="restrictions"` | `back_populates="rules"` |

**YAML/OpenAPI:**

| Old | New |
|---|---|
| `restriction.yaml` (filename) | `rule.yaml` |
| `QueueRestriction` (schema name) | `QueueRule` |
| `RestrictionCreate` (schema name) | `RuleCreate` |
| `RestrictionUpdate` (schema name) | `RuleUpdate` |
| `restriction_type` (property name) | `type` |
| `restriction.yaml#/` (all $ref paths) | `rule.yaml#/` |

**Database:**

| Old | New |
|---|---|
| `queue_restrictions` (table name) | `queue_rules` |
| `restriction_type` (column name) | `type` |

**Test files:**

Same renames as Python identifiers above, applied to test fixtures, mock attributes, and assertions.

### Verification

```bash
# Run all tests to confirm nothing is broken
pytest tests/
```

### Commit

```bash
git add -A && git commit -m "rename restriction to rule across entire codebase"
```

---

## Phase 2 — New Endpoint: Route Handlers

Create the new route handler module and wire it into the OpenAPI spec.

### Create `api/v1/queues/rules.py`

```python
# api/v1/queues/rules.py

from connexion import request

from app.database import PostgresqlDB
from app.database.models import Queue
from app.database.schemas import RuleSchema, RuleCreateSchema
from app.exceptions import NotFound, Conflict, BadRequest
from app.security import role_authorization
from app.security.overrides import queue_owner_override
from app.database.enums import RoleName
from app.database.crud.rules import RuleCRUD


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def get_rules(queue_id: int, **kwargs):
    """GET /queues/{queue_id}/rules — list all rules for a queue."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        rules = await crud.get_rules(queue_id, session=session)

    return [RuleSchema.model_validate(r).model_dump() for r in rules], 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def get_rule(queue_id: int, rule_id: int, **kwargs):
    """GET /queues/{queue_id}/rules/{rule_id} — get a single rule."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        rule = await crud.get_rule(queue_id, rule_id, session=session)

    if not rule:
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return RuleSchema.model_validate(rule).model_dump(), 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def create_rule(queue_id: int, body: dict, **kwargs):
    """POST /queues/{queue_id}/rules — add a single rule to a queue."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    # Validate the rule payload
    try:
        rule_data = RuleCreateSchema.model_validate(body).model_dump(exclude_none=True)
    except Exception as e:
        raise BadRequest(f"Invalid rule data: {e}")

    crud = RuleCRUD()
    async with db.session() as session:
        created = await crud.create_rule(queue_id, rule_data, session=session)

    return RuleSchema.model_validate(created).model_dump(), 201, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def update_rule(queue_id: int, rule_id: int, body: dict, **kwargs):
    """PATCH /queues/{queue_id}/rules/{rule_id} — update a single rule."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    crud = RuleCRUD()
    async with db.session() as session:
        updated = await crud.update_rule(rule_id, queue_id, body, session=session)

    if not updated:
        raise NotFound(f"Rule with ID '{rule_id}' not found in queue '{queue_id}'")

    return RuleSchema.model_validate(updated).model_dump(), 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def delete_rule(queue_id: int, rule_id: int, **kwargs):
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
async def replace_all_rules(queue_id: int, body: dict, **kwargs):
    """PUT /queues/{queue_id}/rules — replace all rules for a queue."""
    db: PostgresqlDB = request.state.db

    queue = await db.get(Queue, id=queue_id)
    if not queue:
        raise NotFound(f"Queue with ID '{queue_id}' not found")

    rules_data = body.get("rules", [])

    # Validate each rule
    validated = []
    for data in rules_data:
        try:
            validated.append(RuleCreateSchema.model_validate(data).model_dump(exclude_none=True))
        except Exception as e:
            raise BadRequest(f"Invalid rule data: {e}")

    crud = RuleCRUD()
    async with db.session() as session:
        created = await crud.upsert_rules(queue_id, validated, session=session)

    return [RuleSchema.model_validate(r).model_dump() for r in created], 200, {"Content-Type": "application/json"}
```

### Add new methods to `app/database/crud/rules.py`

Add these methods to the existing `RuleCRUD` class:

```python
@session_manager()
async def get_rule(
    self,
    queue_id: int,
    rule_id: int,
    session: AsyncSession = None,
) -> QueueRule | None:
    """Fetch a single rule by ID, scoped to a queue."""
    stmt = select(QueueRule).where(
        QueueRule.id == rule_id,
        QueueRule.queue_id == queue_id,
    )
    result = await session.execute(stmt)
    return result.scalars().first()


@session_manager()
async def create_rule(
    self,
    queue_id: int,
    rule_data: dict,
    session: AsyncSession = None,
) -> QueueRule:
    """Create a single rule and append it to the queue's existing rules."""
    # Check for duplicate against existing rules
    existing = await self.get_rules(queue_id, session=session)
    new_key = (
        rule_data["type"],
        rule_data.get("version", "1.0"),
        _normalize_config(rule_data.get("config", {})),
    )
    for existing_rule in existing:
        existing_key = (
            existing_rule.type,
            existing_rule.version,
            _normalize_config(existing_rule.config),
        )
        if existing_key == new_key:
            raise Conflict(
                f"Duplicate rule: {rule_data['type']} v{rule_data.get('version', '1.0')} with the "
                f"same configuration has already been added."
            )

    rule = QueueRule(
        queue_id=queue_id,
        type=rule_data["type"],
        config=rule_data.get("config", {}),
        is_active=rule_data.get("is_active", True),
        version=rule_data.get("version", "1.0"),
    )
    session.add(rule)
    await session.flush()
    await session.refresh(rule)
    return rule


@session_manager()
async def delete_rule(
    self,
    rule_id: int,
    queue_id: int,
    session: AsyncSession = None,
) -> QueueRule | None:
    """Delete a single rule by ID, scoped to a queue."""
    stmt = select(QueueRule).where(
        QueueRule.id == rule_id,
        QueueRule.queue_id == queue_id,
    )
    result = await session.execute(stmt)
    rule = result.scalars().first()

    if not rule:
        return None

    await session.delete(rule)
    await session.flush()
    return rule
```

### Update OpenAPI spec

**`api/v1/spec/paths/queues.yaml`** — Add two new sections:

```yaml
QueueRules:
    get:
        summary: Returns all rules for a queue
        tags:
            - Rules
        security:
            - BearerAuth: []
            - ApiKeyAuth: []
        parameters:
            - $ref: "../parameters/path/queue.yaml#/QueueId"
        responses:
            200:
                $ref: "../responses/200/rule.yaml#/RuleResults"
            401:
                $ref: "../responses/401/generic.yaml#/Unauthorized"
            403:
                $ref: "../responses/403/generic.yaml#/Forbidden"
            404:
                $ref: "../responses/404/generic.yaml#/NotFound"

    post:
        summary: Adds a rule to a queue
        tags:
            - Rules
        security:
            - BearerAuth: []
            - ApiKeyAuth: []
        parameters:
            - $ref: "../parameters/path/queue.yaml#/QueueId"
        requestBody:
            $ref: "../request_bodies/rule.yaml#/RuleCreateBody"
        responses:
            201:
                $ref: "../responses/201/rule.yaml#/RuleCreated"
            400:
                $ref: "../responses/400/generic.yaml#/BadRequest"
            401:
                $ref: "../responses/401/generic.yaml#/Unauthorized"
            403:
                $ref: "../responses/403/generic.yaml#/Forbidden"
            404:
                $ref: "../responses/404/generic.yaml#/NotFound"
            409:
                $ref: "../responses/409/generic.yaml#/Conflict"

    put:
        summary: Replaces all rules for a queue
        tags:
            - Rules
        security:
            - BearerAuth: []
            - ApiKeyAuth: []
        parameters:
            - $ref: "../parameters/path/queue.yaml#/QueueId"
        requestBody:
            $ref: "../request_bodies/rule.yaml#/RulesReplaceBody"
        responses:
            200:
                $ref: "../responses/200/rule.yaml#/RuleResults"
            400:
                $ref: "../responses/400/generic.yaml#/BadRequest"
            401:
                $ref: "../responses/401/generic.yaml#/Unauthorized"
            403:
                $ref: "../responses/403/generic.yaml#/Forbidden"
            404:
                $ref: "../responses/404/generic.yaml#/NotFound"
            409:
                $ref: "../responses/409/generic.yaml#/Conflict"

QueueRuleById:
    get:
        summary: Returns the specified rule
        tags:
            - Rules
        security:
            - BearerAuth: []
            - ApiKeyAuth: []
        parameters:
            - $ref: "../parameters/path/queue.yaml#/QueueId"
            - $ref: "../parameters/path/rule.yaml#/RuleId"
        responses:
            200:
                $ref: "../responses/200/rule.yaml#/RuleResult"
            401:
                $ref: "../responses/401/generic.yaml#/Unauthorized"
            403:
                $ref: "../responses/403/generic.yaml#/Forbidden"
            404:
                $ref: "../responses/404/generic.yaml#/NotFound"

    patch:
        summary: Updates a rule
        tags:
            - Rules
        security:
            - BearerAuth: []
            - ApiKeyAuth: []
        parameters:
            - $ref: "../parameters/path/queue.yaml#/QueueId"
            - $ref: "../parameters/path/rule.yaml#/RuleId"
        requestBody:
            $ref: "../request_bodies/rule.yaml#/RuleUpdateBody"
        responses:
            200:
                $ref: "../responses/200/rule.yaml#/RulePatched"
            400:
                $ref: "../responses/400/generic.yaml#/BadRequest"
            401:
                $ref: "../responses/401/generic.yaml#/Unauthorized"
            403:
                $ref: "../responses/403/generic.yaml#/Forbidden"
            404:
                $ref: "../responses/404/generic.yaml#/NotFound"

    delete:
        summary: Deletes a rule
        tags:
            - Rules
        security:
            - BearerAuth: []
            - ApiKeyAuth: []
        parameters:
            - $ref: "../parameters/path/queue.yaml#/QueueId"
            - $ref: "../parameters/path/rule.yaml#/RuleId"
        responses:
            200:
                $ref: "../responses/200/rule.yaml#/RuleDeleted"
            401:
                $ref: "../responses/401/generic.yaml#/Unauthorized"
            403:
                $ref: "../responses/403/generic.yaml#/Forbidden"
            404:
                $ref: "../responses/404/generic.yaml#/NotFound"
```

Also update `QueueById.patch` in the same file to remove `restrictions` from the whitelisted keys and body schema reference.

**`api/v1/spec/paths/index.yaml`** — Add:

```yaml
/queues/{queue_id}/rules:
    $ref: "./queues.yaml#/QueueRules"

/queues/{queue_id}/rules/{rule_id}:
    $ref: "./queues.yaml#/QueueRuleById"
```

**`api/v1/spec/request_bodies/rule.yaml`** — Create new file:

```yaml
RuleCreateBody:
    description: A JSON payload containing the rule to create
    required: true
    content:
        application/json:
            schema:
                $ref: "../schemas/rule.yaml#/RuleCreate"

RuleUpdateBody:
    description: A JSON payload containing the fields to update
    required: true
    content:
        application/json:
            schema:
                $ref: "../schemas/rule.yaml#/RuleUpdate"

RulesReplaceBody:
    description: A JSON payload containing the full list of rules to replace existing ones
    required: true
    content:
        application/json:
            schema:
                $ref: "../schemas/rule.yaml#/RulesReplace"
```

**`api/v1/spec/schemas/rule.yaml`** — Already has `RuleCreate`, `RuleUpdate`, `QueueRule` (renamed from `QueueRestriction`). Add:

```yaml
RulesReplace:
    title: RulesReplace
    description: Replace all rules for a queue
    type: object
    properties:
        rules:
            type: array
            items:
                $ref: "#/RuleCreate"
            description: List of rules to replace the existing set
    required:
        - rules
```

**`api/v1/spec/schemas/index.yaml`** — Add:

```yaml
Rule:
    $ref: "./rule.yaml#/QueueRule"

RuleCreate:
    $ref: "./rule.yaml#/RuleCreate"

RuleUpdate:
    $ref: "./rule.yaml#/RuleUpdate"

RulesReplace:
    $ref: "./rule.yaml#/RulesReplace"
```

### Create response YAML files

**`api/v1/spec/responses/200/rule.yaml`:**

```yaml
RuleResults:
    description: List of rules
    content:
        application/json:
            schema:
                type: array
                items:
                    $ref: "../../schemas/rule.yaml#/QueueRule"

RuleResult:
    description: Rule
    content:
        application/json:
            schema:
                $ref: "../../schemas/rule.yaml#/QueueRule"

RulePatched:
    description: Rule patch info
    content:
        application/json:
            schema:
                type: object
                properties:
                    message:
                        type: string

RuleDeleted:
    description: Rule deleted info
    content:
        application/json:
            schema:
                type: object
                properties:
                    message:
                        type: string
```

**`api/v1/spec/responses/201/rule.yaml`:**

```yaml
RuleCreated:
    description: Rule created
    content:
        application/json:
            schema:
                $ref: "../../schemas/rule.yaml#/QueueRule"
```

### Create path parameter

**`api/v1/spec/parameters/path/rule.yaml`:**

```yaml
RuleId:
    name: rule_id
    in: path
    required: true
    schema:
        type: integer
    description: The rule ID
```

### Verification

```bash
# Check that the OpenAPI spec loads without errors
python -c "from app.spec import load_spec; spec = load_spec(); print('OpenAPI spec loaded OK')"
```

### Commit

```bash
git add -A && git commit -m "add dedicated /queues/{id}/rules endpoint with full CRUD"
```

---

## Phase 3 — Update Queue Schema & Remove Inline Restrictions

Clean up the queue endpoint and schemas to remove the old `restrictions` key.

### Update `app/database/schemas/queue.py`

Remove `restrictions` from `QueueUpdateSchema`. Keep it on `QueueSchema` so `GET /queues/{id}` still returns rules inline.

```python
class QueueUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_open: Optional[bool] = None
    visibility: Optional[int] = None
    # restrictions removed — use /queues/{id}/rules instead
```

### Update `api/v1/queues/__init__.py`

Remove the `restrictions` handling from the `patch()` function:

1. Remove `"restrictions"` from the `bleach_body` whitelist.
2. Remove the entire `if "restrictions" in body:` block (lines 112-115).
3. Remove the `from app.database.crud.restrictions import RestrictionCRUD` import.

### Update `api/v1/spec/schemas/queue.yaml`

Remove the `restrictions` property from `QueuePatch`.

### Update `api/v1/spec/request_bodies/queue.yaml`

No changes needed — it references `QueuePatch` which no longer has restrictions.

### Verification

```bash
python -c "from app.spec import load_spec; spec = load_spec(); print('OpenAPI spec loaded OK')"
pytest tests/
```

### Commit

```bash
git add -A && git commit -m "remove restrictions key from queue PATCH, use dedicated rules endpoint"
```

---

## Phase 4 — Update Imports & Cross-References

Fix all remaining imports that still reference the old `restriction` module paths.

### Files to update

| File | Change |
|---|---|
| `app/database/models/__init__.py` | `from .queue_restriction import QueueRestriction` → `from .queue_rule import QueueRule` |
| `app/database/schemas/__init__.py` | `from .restriction import ...` → `from .rule import ...` |
| `app/database/__init__.py` or wherever `QueueRestriction` is imported | Update to `QueueRule` |
| `app/database/models/queue.py` | `from .queue_restriction import QueueRestriction` → `from .queue_rule import QueueRule` |
| `app/database/restrictions/` → `app/database/rules/` | All internal imports within the package |
| `api/v1/requests/__init__.py` | `from app.database.restrictions.*` → `from app.database.rules.*` |
| `app/daemon/services/rule_validation.py` | Update any remaining restriction imports |
| `app/daemon/services/queue_request_handler.py` | Update any remaining restriction imports |
| All test files | Update imports |

### Verification

```bash
pytest tests/
```

### Commit

```bash
git add -A && git commit -m "fix all imports after renaming restriction to rule"
```

---

## Phase 5 — Update `POST /requests` to Use New Rule Access Path

The request submission flow (`POST /requests`) currently fetches rules via `RestrictionCRUD.get_restrictions()`. After Phase 1's rename, the CRUD class is `RuleCRUD.get_rules()`. Verify the call sites still work.

### Files to verify

- `api/v1/requests/__init__.py` — `_check_queue_restrictions_phase1()` function. After Phase 1, this should already reference `RuleCRUD.get_rules()`. Verify and adjust if needed.

### Commit (if changes needed)

```bash
git add -A && git commit -m "update request submission to use RuleCRUD.get_rules"
```

---

## Phase 6 — Database Migration

The DB table and column names have changed. Create the migration.

### Migration steps

The table `queue_restrictions` needs to become `queue_rules`, and the column `restriction_type` needs to become `type`.

If using Alembic or similar:

```python
# Migration: rename table and column

def upgrade():
    # Rename column first
    op.rename_column('queue_restrictions', 'restriction_type', 'type')
    # Rename table
    op.rename_table('queue_restrictions', 'queue_rules')

def downgrade():
    op.rename_table('queue_rules', 'queue_restrictions')
    op.rename_column('queue_rules', 'type', 'restriction_type')
```

If no migration tool is used, document the manual SQL:

```sql
ALTER TABLE queue_restrictions RENAME TO queue_rules;
ALTER TABLE queue_rules RENAME COLUMN restriction_type TO type;
```

### Verification

```bash
# Start the app and verify it connects to the renamed table
# Run: python -m app.main
# Check logs for successful DB connection
```

### Commit

```bash
git add -A && git commit -m "add DB migration to rename queue_restrictions to queue_rules and column restriction_type to type"
```

---

## Phase 7 — Frontend Updates

Update the frontend to use the new endpoints instead of the inline `restrictions` key in PATCH requests.

### Files to investigate

Search the frontend for:
- `restrictions` references in API calls
- Queue edit forms that include rule management
- Any direct `PATCH /queues/{id}` calls that include `restrictions`

### Changes needed

- Replace `PATCH /queues/{id}` with `POST /queues/{id}/rules` for adding rules.
- Replace inline `restrictions` in PATCH bodies with dedicated rule management UI.
- Add rule CRUD UI components (list, add, edit, delete rules).
- Update `GET /queues/{id}` response parsing to handle `rules` field (already correct after rename).

### Commit

```bash
git add -A && git commit -m "update frontend to use /queues/{id}/rules endpoints"
```

---

## Phase 8 — Tests

Add comprehensive integration tests for the new endpoint.

### Create `tests/integration/api/test_queue_rules.py`

Test cases:

| Test | Endpoint | Expected |
|---|---|---|
| admin lists rules | `GET /queues/{id}/rules` | 200, list of rules |
| admin gets single rule | `GET /queues/{id}/rules/{rule_id}` | 200, rule object |
| admin creates rule | `POST /queues/{id}/rules` | 201, created rule |
| admin updates rule | `PATCH /queues/{id}/rules/{rule_id}` | 200, updated rule |
| admin deletes rule | `DELETE /queues/{id}/rules/{rule_id}` | 200, success message |
| admin replaces all rules | `PUT /queues/{id}/rules` | 200, list of rules |
| owner manages rules | `POST/PUT/PATCH/DELETE` | 200/201 |
| non-owner gets 403 | All write endpoints | 403 |
| missing queue returns 404 | All endpoints with bad queue_id | 404 |
| missing rule returns 404 | GET/PATCH/DELETE with bad rule_id | 404 |
| duplicate rule returns 409 | POST with duplicate config | 409 |
| invalid rule config returns 400 | POST with bad config | 400 |
| PATCH queue no longer affects rules | PATCH metadata only | rules unchanged |

### Update existing tests

- `tests/integration/api/test_restrictions.py` → `tests/integration/api/test_rules.py` (already renamed in Phase 1).
- Update any test that calls `PATCH /queues/{id}` with `restrictions` to use the new endpoints.

### Verification

```bash
pytest tests/ -v
```

### Commit

```bash
git add -A && git commit -m "add comprehensive integration tests for /queues/{id}/rules endpoint"
```

---

## Phase 9 — Update Documentation

Update `docs/rule_engine_v2.md` to reflect the new endpoint structure, or create `docs/rule_engine_v3.md` as a reference for API users.

### Update `docs/rule_engine_v2.md`

Add an "API Endpoints" section documenting:

```markdown
## API Endpoints

### Manage Rules

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/queues/{queue_id}/rules` | List all rules for a queue |
| GET | `/api/v1/queues/{queue_id}/rules/{rule_id}` | Get a specific rule |
| POST | `/api/v1/queues/{queue_id}/rules` | Add a rule to a queue |
| PATCH | `/api/v1/queues/{queue_id}/rules/{rule_id}` | Update a rule |
| DELETE | `/api/v1/queues/{queue_id}/rules/{rule_id}` | Delete a rule |
| PUT | `/api/v1/queues/{queue_id}/rules` | Replace all rules |

All endpoints require ADMIN role or queue ownership.
```

### Verify OpenAPI spec

```bash
python -c "from app.spec import load_spec; spec = load_spec(); import yaml; print(yaml.dump(spec, default_flow_style=False))" | grep -A2 "/queues/{queue_id}/rules"
```

### Commit

```bash
git add -A && git commit -m "update documentation with new rules endpoint references"
```

---

## Summary of Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/queues/{queue_id}/rules` | List all rules |
| `GET` | `/api/v1/queues/{queue_id}/rules/{rule_id}` | Get a rule |
| `POST` | `/api/v1/queues/{queue_id}/rules` | Add a rule |
| `PATCH` | `/api/v1/queues/{queue_id}/rules/{rule_id}` | Update a rule |
| `DELETE` | `/api/v1/queues/{queue_id}/rules/{rule_id}` | Delete a rule |
| `PUT` | `/api/v1/queues/{queue_id}/rules` | Replace all rules |

**Authorization:** `ADMIN` role or queue owner (via `queue_owner_override`).

**Response format:** All rule endpoints return `RuleSchema` objects (with `id`, `queue_id`, `type`, `config`, `is_active`, `version`, `created_at`, `updated_at`).
