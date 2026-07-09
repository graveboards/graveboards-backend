# Modding Queue Rule Engine v2 — Architecture Plan

> **Status**: Proposed — awaiting implementation approval
> **Scope**: Next-generation rule engine for Graveboards modding queues
> **Date**: 2026-07-07

---

## 1. Purpose

Replace the current flat restriction system (rate limit, cooldown, blacklist) with a composable, extensible rule engine that can inspect both user conditions and beatmap metadata. The engine must support hundreds of rule types maintained by multiple contributors, with clean separation between synchronous fast-path validation and asynchronous slow-path validation.

---

## 2. Current State

The existing restriction system lives at `app/database/restrictions/` and consists of:

- **Three validators**: `rate_limit`, `cooldown`, `blacklist` — all user-only, Redis-backed, synchronous.
- **Flat registry**: A simple `dict[str, type]` mapping restriction type names to validator classes.
- **Flat config**: Each validator receives a `config: dict[str, Any]` with no schema enforcement beyond basic Pydantic validation at the API layer.
- **Synchronous execution**: All restrictions are checked in `_check_queue_restrictions()` during `POST /requests`, blocking the HTTP response.
- **No beatmap inspection**: Validators cannot see beatmap metadata (BPM, star rating, AR, genre, etc.).
- **No osu! API lookups**: There is no mechanism to query osu! for ranked status or song identity.

The osu! API client (`app/osu_api/client/osu_api_client.py`) is already available with 1-hour Redis caching for beatmapset data. The database stores full beatmapset and beatmap snapshots with all metadata fields. The daemon infrastructure (`app/daemon/services/`) already supports background task processing via Redis pub/sub.

---

## 3. Architecture Overview

### 3.1 Two-Phase Validation

Validation is split into two phases to separate fast synchronous checks from slow asynchronous lookups.

```
POST /requests
  │
  ├─ Phase 1: Synchronous (blocks HTTP response)
  │    ├─ Tier 1: User-only validators (Redis-backed, <1ms each)
  │    └─ Tier 2: Beatmap metadata validators (in-memory, <5ms each)
  │    └─ If ANY validator rejects → 403 Forbidden immediately
  │
  └─ Phase 2: Asynchronous (non-blocking, after queueing)
       ├─ Tier 3: osu! API / database validators (seconds per rule)
       └─ If ANY validator rejects → Request status = REJECTED, user notified
```

**Phase 1** runs during request submission. All Tier 1 and Tier 2 validators execute synchronously. They are fast because they read from in-memory objects (the beatmapset already fetched from osu! at request time) and Redis. If any reject, the user gets an immediate 403.

**Phase 2** runs after the request is queued for processing. Tier 3 validators are dispatched to a dedicated daemon service that processes them in the background. If a Tier 3 validator rejects the request, the request status is updated to `REJECTED` and the user is notified.

### 3.2 Validator Tiers

| Tier | What it inspects | Where it runs | Latency | Examples |
|------|-----------------|---------------|---------|----------|
| **1** | User identity only | Synchronous (Phase 1) | <1ms | rate_limit, cooldown, blacklist |
| **2** | Beatmap metadata | Synchronous (Phase 1) | <5ms | duration, star rating, AR, genre, BPM, storyboard, video, difficulty count |
| **3** | osu! API / external state | Asynchronous (Phase 2) | 1–5s | never_ranked, unique_artist_title |

### 3.3 Rule Composition

Rules support full **AND / OR / NOT** composition via a `composite` rule type:

```json
{
  "type": "composite",
  "config": {
    "operator": "and",
    "rules": [
      {
        "type": "beatmap_star_rating",
        "config": { "min": 5.8, "max": 6.8 }
      },
      {
        "type": "composite",
        "config": {
          "operator": "or",
          "rules": [
            { "type": "beatmap_genre", "config": { "genre_ids": [4, 5] } },
            { "type": "beatmap_genre", "config": { "genre_ids": [10] } }
          ]
        }
      }
    ]
  }
}
```

This allows queue owners to express arbitrarily complex logic. The engine evaluates composite rules recursively, short-circuiting where possible (e.g., AND stops at first failure, OR stops at first success).

---

## 4. Rule Representation

### 4.1 Wire Format: JSON

Rules are stored in the `queue_restrictions` table as JSON in the `config` column. JSON is the wire format for:

- Database persistence
- API serialization (OpenAPI schemas)
- Queue management UI configuration

### 4.2 In-Memory Representation: Expression Trees

At validation time, each rule's JSON config is converted into an in-memory expression tree. Each rule type has a corresponding tree node class that knows how to evaluate itself against the `ExecutionContext`.

```
RuleNode (base)
├── AtomicRuleNode          # Leaf rules: beatmap_duration, beatmap_star_rating, etc.
└── CompositeRuleNode       # AND / OR / NOT composition
    ├── AndNode
    ├── OrNode
    └── NotNode
```

This separation means:
- Config schemas (Pydantic) validate the JSON at API time.
- Expression tree nodes evaluate the rule at validation time.
- Adding a new rule type means adding a new config schema + a new tree node — no changes to the engine core.

### 4.3 Rule Schema Structure

Every rule stored in the database has this structure:

```json
{
  "id": 42,
  "queue_id": 1,
  "type": "beatmap_duration",
  "config": {
    "max_seconds": 180,
    "logic": "max"
  },
  "is_active": true,
  "version": "1.0"
}
```

Composite rules wrap other rules:

```json
{
  "id": 43,
  "queue_id": 1,
  "type": "composite",
  "config": {
    "operator": "and",
    "rules": [
      { "type": "beatmap_star_rating", "config": { "min": 5.8, "max": 6.8 } },
      { "type": "beatmap_duration", "config": { "max_seconds": 180 } }
    ]
  },
  "is_active": true,
  "version": "1.0"
}
```

### 4.4 Why JSON + Expression Trees, Not a DSL?

| Approach | Pros | Cons |
|----------|------|------|
| Custom DSL | Expressive, parseable | New language to learn, custom parser, syntax errors |
| Python `eval` | Flexible | Security risk, no validation, no IDE support |
| Full AST (e.g., `ast` module) | Type-safe | Overkill for declarative rules, rigid |
| **JSON + expression trees** | **Self-documenting, validates with Pydantic, composes naturally, no custom parser** | **Slightly more code per rule type** |

JSON + expression trees is the best trade-off. Each rule type's config is a small, self-documenting JSON object validated by Pydantic. The expression tree is a thin evaluation layer on top.

---

## 5. ExecutionContext

The `ExecutionContext` is the central data bridge between the beatmap data and the validators. It replaces the current flat parameters (`queue_id`, `user_id`, `db`, `redis`, `config`) with a structured context object.

```python
class ExecutionContext:
    # Identity
    queue_id: int
    user_id: int

    # Beatmap data (populated from osu! API at request time)
    beatmapset: BeatmapsetOsuApiSchema | None
    beatmaps: list[BeatmapOsuApiSchema] | None

    # Database snapshots (populated if beatmapset was archived)
    beatmapset_snapshot: BeatmapsetSnapshot | None
    beatmap_snapshots: list[BeatmapSnapshot] | None

    # Services
    db: PostgresqlDB
    redis: RedisClient
    osu_client: OsuAPIClient | None    # Only available in Phase 2
    session: AsyncSession | None       # Only available in Phase 2

    # Metadata providers (resolved lazily, cached per context)
    metadata_providers: dict[str, MetadataProvider]
    _provider_cache: dict[str, dict]
```

### 5.1 Data Flow

1. `POST /requests` fetches the beatmapset from osu! API (already done at line 94-95 of `api/v1/requests/__init__.py`).
2. The engine builds an `ExecutionContext` with the fetched beatmapset data.
3. Validators read from `context.beatmapset` and `context.beatmaps` — no refetching.
4. For Phase 2, the engine passes the `osu_client` and `session` to Tier 3 validators.

### 5.2 Lazy Metadata Resolution

Metadata providers are resolved lazily and cached within a single `ExecutionContext`:

```python
async def get_metadata(self, provider_name: str) -> dict:
    if provider_name not in self._provider_cache:
        provider = self.metadata_providers[provider_name]
        self._provider_cache[provider_name] = await provider.resolve(self)
    return self._provider_cache[provider_name]
```

This prevents redundant work when multiple rules in the same request need the same derived data (e.g., two rules both need the normalized song identity).

---

## 6. Metadata Providers

Metadata providers are pluggable services that compute derived data for rule evaluation. They answer questions like "what is the canonical song identity for ranking comparison?" or "what is the max star rating across all difficulties?"

### 6.1 Provider Interface

```python
class MetadataProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def resolve(self, context: ExecutionContext) -> dict[str, Any]: ...
```

### 6.2 Built-in Providers

| Provider | Purpose | Output |
|----------|---------|--------|
| `SongIdentityProvider` | Normalizes artist/title for osu! API ranking comparison | `{ artist, artist_unicode, title, title_unicode, normalized_artist, normalized_title, duration }` |
| `BeatmapStatsProvider` | Computes aggregate stats across all difficulties | `{ min_sr, max_sr, avg_sr, min_ar, max_ar, min_od, max_od, min_hp, max_hp, min_drain, max_drain, min_bpm, max_bpm, difficulty_count, modes }` |
| `CreatorIdentityProvider` | Resolves creator usernames from user IDs | `{ artist_creator_id, artist_creator_username, mapper_ids, mapper_usernames }` |
| `DurationProvider` | Computes normalized duration handling version cuts | `{ original_duration, normalized_duration, has_version_marker }` |

### 6.3 Song Identity Normalization (Provider Detail)

The `SongIdentityProvider` is critical for the "never ranked" check. It must handle:

1. **Bilingual matching**: Compare both `artist`/`artist_unicode` and `title`/`title_unicode` against osu! API results. osu! data may be in romaji or native script.
2. **Version marker normalization**: Strip markers like `TV Size`, `Extended ver.`, `Remix`, `Cut version`, `Nightcore ver.`, `Radio Edit`, `Album Edit`, `Full ver.`, `Instrumental`, etc.
3. **Punctuation/whitespace normalization**: Collapse whitespace, strip punctuation, lowercase for comparison.

The normalization algorithm:

```
1. Take artist + title (both original and unicode variants)
2. Apply version marker regex removal:
   - Patterns: (TV Size|Extended ver\.?|Remix|Cut version|Nightcore ver\.?|Radio Edit|Album Edit|Full ver\.?|Instrumental|Single Version|Radio Version|7" Version|12" Version|Club Mix|Dub Mix|Acoustic Version|Live Version)\.?\s*$
3. Normalize whitespace and punctuation
4. Produce normalized (artist, title) pair for comparison
```

This normalized pair is used to query the osu! API's `search_beatmapsets()` endpoint for ranked songs.

---

## 7. Validator Organization

### 7.1 Directory Structure

```
app/database/restrictions/
├── base.py                          # Abstract base classes
├── registry.py                      # Validator registry (tier-aware)
├── exceptions.py                    # RestrictionViolationError
├── context.py                       # ExecutionContext
├── engine.py                        # RuleEngine orchestrator
├── validators/
│   ├── __init__.py
│   ├── user/                        # Tier 1: user-only (existing, refactored)
│   │   ├── rate_limit.py
│   │   ├── cooldown.py
│   │   └── blacklist.py
│   ├── beatmap/                     # Tier 2: beatmap metadata (NEW)
│   │   ├── duration.py
│   │   ├── star_rating.py
│   │   ├── ar_range.py
│   │   ├── od_range.py
│   │   ├── hp_range.py
│   │   ├── cs_range.py
│   │   ├── drain_range.py
│   │   ├── bpm.py
│   │   ├── genre.py
│   │   ├── language.py
│   │   ├── difficulty_count.py
│   │   ├── storyboard.py
│   │   ├── video.py
│   │   ├── ranked_status.py
│   │   ├── creator.py
│   │   ├── mode.py                  # Game mode matching
│   │   ├── tags.py                  # Tag-based filtering
│   │   ├── length.py                # Total length / hit length
│   │   └── combinations.py          # Pre-built common combinations
│   ├── database/                    # Tier 3: osu! API backed (NEW)
│   │   ├── never_ranked.py          # "song has never been ranked"
│   │   ├── unique_artist_title.py   # "same song already ranked"
│   │   └── osu_api_lookup.py        # Generic osu! API lookup helper
│   └── metadata/                    # Metadata providers (NEW)
│       ├── __init__.py
│       ├── song_identity.py
│       ├── beatmap_stats.py
│       ├── creator_identity.py
│       └── duration.py
└── engine/                          # Engine internals (NEW)
    ├── __init__.py
    ├── evaluator.py                 # Expression tree evaluation
    ├── phase1_runner.py             # Synchronous phase runner
    └── phase2_runner.py             # Asynchronous phase runner
```

### 7.2 Base Classes

```python
class RestrictionBase(ABC):
    """Base for all restriction types."""
    restriction_type: str
    config_schema: type[BaseModel] | None = None
    supported_versions: set[str] = {"1.0"}

    async def validate_config(self, config: dict) -> dict:
        """Validate config against Pydantic schema. Called at API time."""
        if self.config_schema:
            validated = self.config_schema(**config)
            return validated.model_dump(exclude_none=True)
        return config

    async def check(self, context: ExecutionContext) -> None:
        """Main entry point. Delegates based on tier."""
        ...


class BeatmapRestrictionBase(RestrictionBase):
    """Base for Tier 2 validators that inspect beatmap metadata."""

    async def check(self, context: ExecutionContext) -> None:
        if not context.beatmapset:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset metadata not available"
            )
        await self.check_beatmap(context)

    @abstractmethod
    async def check_beatmap(self, context: ExecutionContext) -> None:
        ...


class DatabaseRestrictionBase(RestrictionBase):
    """Base for Tier 3 validators requiring osu! API lookups."""

    async def check(self, context: ExecutionContext) -> None:
        if not context.osu_client:
            raise RestrictionViolationError(
                self.restriction_type,
                "This restriction requires osu! API access (Phase 2 only)"
            )
        await self.check_database(context)

    @abstractmethod
    async def check_database(self, context: ExecutionContext) -> None:
        ...
```

### 7.3 Existing Validators (Refactored)

The existing `rate_limit`, `cooldown`, and `blacklist` validators are refactored to use `ExecutionContext`:

```python
class RateLimitRestriction(RestrictionBase):
    restriction_type = "rate_limit"

    async def check(self, context: ExecutionContext) -> None:
        # ... uses context.user_id, context.db, context.redis, context.config
```

No behavior changes — only the parameter signature changes.

### 7.4 New Tier 2 Validators

Each validator follows the same pattern: read from `context.beatmapset` / `context.beatmaps`, raise `RestrictionViolationError` if violated.

**Example: `beatmap_duration`**

```json
// Config
{ "max_seconds": 180, "logic": "max" }
// or
{ "min_seconds": 30, "max_seconds": 200, "logic": "all" }
```

```python
class DurationRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_duration"
    config_schema = DurationConfig  # Pydantic model

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "max")

        if logic == "max":
            # Use the longest beatmap's total_length
            lengths = [b.total_length for b in context.beatmaps]
            max_length = max(lengths) if lengths else 0
            if max_length > config["max_seconds"]:
                raise RestrictionViolationError(...)
        elif logic == "all":
            for beatmap in context.beatmaps:
                if beatmap.total_length < config.get("min_seconds", 0) or \
                   beatmap.total_length > config["max_seconds"]:
                    raise RestrictionViolationError(...)
```

**Example: `mode` (game mode matching)**

```json
{ "allowed_modes": ["osu"] }
```

```python
class ModeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_mode"

    async def check_beatmap(self, context: ExecutionContext) -> None:
        allowed = set(context.config["allowed_modes"])
        actual_modes = {b.mode for b in context.beatmaps}
        if not actual_modes.issubset(allowed):
            raise RestrictionViolationError(
                self.restriction_type,
                f"Beatmapset contains unsupported modes: {actual_modes - allowed}"
            )
```

### 7.5 New Tier 3 Validators

**Example: `never_ranked` — using osu! API, NOT local database**

```json
{
  "ruleset": "osu",
  "normalize_versions": true,
  "async_validation": true
}
```

```python
class NeverRankedRestriction(DatabaseRestrictionBase):
    restriction_type = "never_ranked"

    async def check_database(self, context: ExecutionContext) -> None:
        # 1. Resolve song identity via provider
        identity = await context.get_metadata("song_identity")

        # 2. Search osu! API for ranked beatmapsets matching this identity
        #    Use search_beatmapsets() with status="ranked,approved,qualified,loved"
        #    Filter by ruleset (game mode)
        results = await context.osu_client.search_beatmapsets(
            status="ranked,approved,qualified,loved",
            # ... search parameters derived from identity
        )

        # 3. Check if any result matches the normalized artist/title
        for result in results:
            if self._match_identity(result, identity):
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Song '{identity['artist']} - {identity['title']}' is already ranked"
                )
```

**Why osu! API and not local DB**: The Graveboards database may not contain all beatmaps for a given song. Using the osu! API as the source of truth ensures we never miss a ranked version. The local DB is used for caching results (Redis, 24h TTL) to avoid redundant API calls.

---

## 8. Engine Orchestrator

The `RuleEngine` is the top-level coordinator. It:

1. Loads active restrictions for a queue from the database.
2. Validates each rule's config against its Pydantic schema.
3. Separates rules into Phase 1 (Tier 1 + Tier 2) and Phase 2 (Tier 3).
4. Executes Phase 1 synchronously during request submission.
5. Dispatches Phase 2 rules to the async daemon.

```python
class RuleEngine:
    def __init__(self):
        self.registry = get_registry()  # tier-aware registry
        self.providers = self._load_providers()

    async def validate_request(
        self,
        queue_id: int,
        user_id: int,
        beatmapset: BeatmapsetOsuApiSchema,
        beatmaps: list[BeatmapOsuApiSchema],
        db: PostgresqlDB,
        redis: RedisClient,
    ) -> None:
        """Phase 1: synchronous validation."""
        restrictions = await self._load_active_restrictions(queue_id)
        context = ExecutionContext(
            queue_id=queue_id,
            user_id=user_id,
            beatmapset=beatmapset,
            beatmaps=beatmaps,
            db=db,
            redis=redis,
            osu_client=None,         # Not available in Phase 1
            session=None,
            metadata_providers=self.providers,
        )
        await self._execute_phase(context, restrictions, phase=1)

    async def validate_async(
        self,
        request_id: int,
        queue_id: int,
        beatmapset: BeatmapsetOsuApiSchema,
        beatmaps: list[BeatmapOsuApiSchema],
        db: PostgresqlDB,
        redis: RedisClient,
        osu_client: OsuAPIClient,
    ) -> None:
        """Phase 2: asynchronous validation."""
        restrictions = await self._load_active_restrictions(queue_id)
        phase2_rules = [r for r in restrictions if self._is_async(r)]

        async with OsuAPIClient(redis) as client:
            context = ExecutionContext(
                queue_id=queue_id,
                user_id=...,  # from request record
                beatmapset=beatmapset,
                beatmaps=beatmaps,
                db=db,
                redis=redis,
                osu_client=client,
                session=await db.session(),
                metadata_providers=self.providers,
            )
            await self._execute_phase(context, phase2_rules, phase=2)
```

### 8.1 Composite Rule Evaluation

```python
class CompositeEvaluator:
    @staticmethod
    async def evaluate(node: CompositeRuleNode, context: ExecutionContext) -> bool:
        if isinstance(node, AndNode):
            for rule in node.rules:
                if not await rule.evaluate(context):
                    return False  # Short-circuit: AND fails fast
            return True

        elif isinstance(node, OrNode):
            for rule in node.rules:
                if await rule.evaluate(context):
                    return True  # Short-circuit: OR succeeds fast
            return False

        elif isinstance(node, NotNode):
            return not await node.rule.evaluate(context)
```

### 8.2 Depth Limiting

Composite rules are capped at depth 10 to prevent stack overflow from malformed configs:

```python
async def evaluate(self, context: ExecutionContext, depth: int = 0) -> bool:
    if depth > MAX_COMPOSITE_DEPTH:  # 10
        raise RestrictionViolationError(
            "composite", "Rule nesting depth exceeds maximum (10)"
        )
    # ... recursive evaluation
```

---

## 9. Asynchronous Validation Pipeline

### 9.1 Flow

```
POST /requests
  │
  ├─ Phase 1 validators run synchronously
  │    └─ If rejected → 403 returned to user
  │
  └─ Request queued for processing (existing flow)
       │
       └─ QueueRequestHandler daemon archives beatmapset
            │
            └─ Publishes Phase 2 validation task to Redis
                 │
                 └─ RuleValidationService picks up task
                      ├─ Runs Tier 3 validators
                      ├─ If rejected → update Request.status = REJECTED
                      └─ User notified (see Section 9.3)
```

### 9.2 New Daemon Service

```python
class RuleValidationService(ScheduledService):
    """Processes Tier 3 rule validations asynchronously."""
    CHANNEL = ChannelName.QUEUE_REQUEST_VALIDATION_TASKS
    JOB_NAME = "rule-validation"

    async def _execute_job(self, record_id: int):
        # 1. Load task from Redis
        # 2. Build ExecutionContext with osu_client
        # 3. Run RuleEngine.validate_async()
        # 4. If rejected → update request status
        # 5. Publish notification event
```

### 9.3 User Notification

When a Tier 3 validator rejects a request:

1. The request's `status` is set to `REJECTED` (-1).
2. The rejection reason (restriction type + detail message) is stored in the request record or a new `rejection_reason` field.
3. The frontend polls `GET /requests/{id}` and displays the rejection reason to the user.
4. The user can see the rejection reason in their "My Requests" page.

```python
# Request model addition
class Request(Base):
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
```

The frontend (Next.js) displays the rejection reason next to the request in the user's request list, with a message like:
> "This request was rejected because: Song 'Artist - Title' is already ranked on osu! standard."

---

## 10. Game Mode Matching

osu! has four game modes: `osu`, `taiko`, `fruits`, `mania`. Each beatmap within a beatmapset belongs to one mode. A rule engine must support:

- **Mode filtering**: "only accept osu! mode maps"
- **Mode exclusion**: "reject taiko maps"
- **Multi-mode rules**: "accept any mode" or "accept osu and taiko only"

The `mode` validator checks the `mode` field on each `BeatmapOsuApiSchema` (or `BeatmapSnapshot`):

```python
class ModeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_mode"

    async def check_beatmap(self, context: ExecutionContext) -> None:
        allowed = set(context.config["allowed_modes"])
        actual_modes = {b.mode for b in context.beatmaps}
        if not actual_modes.issubset(allowed):
            unsupported = actual_modes - allowed
            raise RestrictionViolationError(
                self.restriction_type,
                f"Beatmapset contains unsupported modes: {unsupported}"
            )
```

For Tier 3 validators (e.g., "never ranked"), the osu! API search is filtered by the same mode to ensure we only compare against ranked maps in the same game mode.

---

## 11. Rule Versioning

### 11.1 Version Field

The `queue_restrictions` table gains a `version` column:

```python
class QueueRestriction(Base):
    version: Mapped[str] = mapped_column(String(10), default="1.0")
```

### 11.2 Version Semantics

- Each validator declares `supported_versions: set[str]`.
- When a rule type's config schema changes (new field, removed field, behavior change), the version increments (e.g., `1.0` → `1.1`).
- Existing rules with old versions continue to work as long as the validator supports them.
- Rules with unsupported versions are flagged during validation and the queue owner is notified.

### 11.3 Migration

When the engine upgrades:
- Validators with backward-compatible changes support multiple versions.
- Validators with breaking changes require queue owners to re-save their rules through the UI.
- The API returns a `rule_versions` endpoint listing supported versions for each rule type.

---

## 12. Performance Considerations

### 12.1 Synchronous Path (Phase 1)

| Concern | Mitigation |
|---------|-----------|
| Latency per rule | <5ms per Tier 2 rule (pure in-memory) |
| Cumulative latency | 50 rules × 5ms = 250ms max (acceptable for HTTP) |
| No refetching | Beatmapset data passed by reference from initial osu! API call |
| No extra DB queries | Tier 2 reads from in-memory objects only |
| Short-circuit | Composite AND stops at first failure; OR stops at first success |
| Config validation | Pydantic schemas cached per rule type, validated once at config time |

### 12.2 Asynchronous Path (Phase 2)

| Concern | Mitigation |
|---------|-----------|
| osu! API rate limits | Existing `@rate_limit(min_interval=0.5, limit_per_window=120)` decorator |
| Redundant lookups | Redis cache for song identity → ranked status (TTL: 24h) |
| Concurrent validation | Daemon processes tasks sequentially per queue_id (deduplication) |
| Timeout | 30-second timeout per Tier 3 validator; failure = request accepted (fail-open) |
| osu! API unavailability | Fail-open: if osu! API is unreachable, the request is accepted (not blocked) |

### 12.3 Failure Handling

Tier 3 validators fail-open: if the osu! API is unreachable or a validator throws an unexpected exception, the request is **accepted** rather than rejected. This prevents the system from blocking legitimate submissions when external services are down. The failure is logged for monitoring.

---

## 13. Security Considerations

### 13.1 Config Injection Prevention

- All configs are validated against Pydantic schemas before storage.
- No raw Python execution — configs are data, not code.
- Composite rules are validated recursively for depth and structure.
- The `type` field is checked against the registry — unknown types are rejected.

### 13.2 Resource Limits

| Limit | Value | Rationale |
|-------|-------|-----------|
| Max active rules per queue | 50 | Prevents abuse and excessive validation time |
| Max composite depth | 10 | Prevents stack overflow |
| Max rules per request (Phase 1) | 50 × 5ms = 250ms | Acceptable HTTP latency |
| Max rules per request (Phase 2) | 50 × 5s = 250s | Processed asynchronously, user doesn't wait |
| Tier 3 validator timeout | 30s per rule | Prevents hanging tasks |
| osu! API rate limit | 120 req/min (existing) | Respects osu! API terms |

### 13.3 osu! API Security

- All osu! API calls use the existing OAuth2 client credentials flow.
- Rate limiting is enforced via the existing `@rate_limit` decorator.
- Redis deduplication prevents redundant lookups for the same song.
- Cached results have a 24-hour TTL (ranked status rarely changes).

---

## 14. Testing Strategy

### 14.1 Unit Tests

Each validator gets a unit test file:

```
tests/unit/restrictions/
├── test_context.py                  # ExecutionContext construction and metadata resolution
├── test_engine.py                   # RuleEngine orchestration (phase routing, composite eval)
├── test_composite_evaluator.py      # AND/OR/NOT short-circuit behavior
├── test_song_identity_provider.py   # Normalization with real osu! song name variations
├── test_beatmap_stats_provider.py   # Aggregate stats computation
├── user/
│   ├── test_rate_limit.py
│   ├── test_cooldown.py
│   └── test_blacklist.py
├── beatmap/
│   ├── test_duration.py
│   ├── test_star_rating.py
│   ├── test_mode.py
│   ├── test_genre.py
│   ├── test_bpm.py
│   └── ... (one per new validator)
└── database/
    └── test_never_ranked.py         # Mocked osu! API responses
```

Tests use the existing `TestClientWithMocks` pattern with mocked `db` and `redis`, plus a real `ExecutionContext` with mock beatmapset data.

### 14.2 Integration Tests

Extended `tests/integration/api/test_restrictions.py`:

- Beatmap metadata validation during request submission (Phase 1)
- Async validation pipeline (Phase 2) with mocked daemon
- Composite rule evaluation end-to-end
- Game mode filtering

### 14.3 Song Identity Provider Tests

Test cases for normalization:

| Input Title | Normalized | Expected Match |
|------------|-----------|---------------|
| "Artist - Song (TV Size)" | "Artist - Song" | "Artist - Song" |
| "Artist - Song (Extended ver.)" | "Artist - Song" | "Artist - Song" |
| "Artist - Song (Remix)" | "Artist - Song" | "Artist - Song" |
| "Artist - Song (Nightcore Ver.)" | "Artist - Song" | "Artist - Song" |
| "Artist - Song (Radio Edit)" | "Artist - Song" | "Artist - Song" |
| "Artist - Song" | "Artist - Song" | "Artist - Song" |
| "Artist_unicode - Song_unicode" | "artist_unicode - song_unicode" | "artist - song" (bilingual) |

### 14.4 Performance Tests

- Benchmark Phase 1 validation: target <10ms for 10 rules.
- Benchmark Phase 2 validation throughput under concurrent load.
- Benchmark osu! API deduplication: 100 requests for same song should produce 1 API call.

---

## 15. Frontend Changes

### 15.1 Request Rejection Display

The frontend already displays request status (Pending / Accepted / Rejected). The `rejection_reason` field adds context:

```tsx
// In the request list item
{request.status === -1 && request.rejection_reason && (
  <div className="text-red-500 text-sm">
    {request.rejection_reason}
  </div>
)}
```

### 15.2 Queue Management UI

The queue management page (`/queues/[id]/manage`) needs a rule editor UI:

- List current rules with type, config summary, and active toggle.
- Add new rule button → rule type selector → config form (generated from Pydantic schema).
- Composite rule builder with drag-and-drop or nested form for AND/OR/NOT.
- Show supported rule versions and migration prompts for outdated rules.

This is outside the scope of the backend architecture but should be planned in parallel.

---

## 16. Open API Schema Changes

### 16.1 New Restriction Types in OpenAPI

The OpenAPI spec (`api/v1/spec/schemas/restriction.yaml`) gains new restriction type definitions with full config schemas:

- `beatmap_duration`, `beatmap_star_rating`, `beatmap_ar_range`, `beatmap_od_range`, `beatmap_hp_range`, `beatmap_cs_range`, `beatmap_drain_range`
- `beatmap_bpm`, `beatmap_genre`, `beatmap_language`, `beatmap_mode`, `beatmap_difficulty_count`, `beatmap_storyboard`, `beatmap_video`, `beatmap_ranked_status`, `beatmap_creator`, `beatmap_tags`, `beatmap_length`
- `composite` (with nested rules)
- `never_ranked`, `unique_artist_title`

### 16.2 New Request Field

The `Request` schema gains `rejection_reason`:

```yaml
Request:
  type: object
  properties:
    rejection_reason:
      type: string
      nullable: true
      description: "Reason provided by async validators if request was rejected"
```

---

## 17. Database Schema Changes

### 17.1 QueueRestriction Migration

```sql
ALTER TABLE queue_restrictions ADD COLUMN version VARCHAR(10) DEFAULT '1.0';
```

### 17.2 Request Migration

```sql
ALTER TABLE requests ADD COLUMN rejection_reason TEXT;
```

### 17.3 New Redis Channels

```python
ChannelName.QUEUE_REQUEST_VALIDATION_TASKS = "queue_request_validation_tasks"
```

---

## 18. File Change Summary

| File / Directory | Change |
|-----------------|--------|
| `docs/rule_engine_v2.md` | **This file** — architecture plan |
| `app/database/restrictions/base.py` | Refactor: add `BeatmapRestrictionBase`, `DatabaseRestrictionBase` |
| `app/database/restrictions/registry.py` | Enhance: tier-aware registry, version support |
| `app/database/restrictions/exceptions.py` | Minor: add rule version to error messages |
| `app/database/restrictions/context.py` | **NEW** — `ExecutionContext` |
| `app/database/restrictions/engine.py` | **NEW** — `RuleEngine` orchestrator |
| `app/database/restrictions/validators/user/` | Refactor: adapt to `ExecutionContext` |
| `app/database/restrictions/validators/beatmap/` | **NEW** — 15+ beatmap metadata validators |
| `app/database/restrictions/validators/database/` | **NEW** — osu! API validators |
| `app/database/restrictions/validators/metadata/` | **NEW** — metadata providers |
| `app/database/restrictions/engine/` | **NEW** — evaluator, phase runners |
| `app/database/models/queue_restriction.py` | Add `version` column |
| `app/database/models/request.py` | Add `rejection_reason` column |
| `app/database/schemas/restriction.py` | Add config schemas for all new rule types |
| `app/database/schemas/request.py` | Add `rejection_reason` to schemas |
| `app/database/crud/restrictions.py` | Support version in CRUD |
| `app/redis/enums.py` | Add `QUEUE_REQUEST_VALIDATION_TASKS` channel |
| `app/daemon/services/` | **NEW** — `RuleValidationService` |
| `api/v1/requests/__init__.py` | Split into Phase 1 + Phase 2 dispatch |
| `api/v1/spec/schemas/restriction.yaml` | Add new restriction type definitions |
| `api/v1/spec/schemas/request.yaml` | Add `rejection_reason` field |
| `tests/unit/restrictions/` | **NEW** — unit tests for all validators |
| `tests/integration/api/test_restrictions.py` | Extend with beatmap + async tests |

---

## 19. Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] `ExecutionContext` class
- [ ] Refactor existing validators (rate_limit, cooldown, blacklist) to use `ExecutionContext`
- [ ] Enhanced registry with tier awareness
- [ ] Pydantic config schemas for all existing rule types
- [ ] Unit tests for refactored validators

### Phase 2: Tier 2 Validators (Week 2)

- [ ] Beatmap metadata validators (duration, star_rating, ar_range, bpm, genre, language, mode, etc.)
- [ ] Composite rule evaluator (AND/OR/NOT)
- [ ] Metadata providers (SongIdentity, BeatmapStats, CreatorIdentity, Duration)
- [ ] Unit tests for all new validators
- [ ] Integration tests for Phase 1 validation flow

### Phase 3: Tier 3 Validators + Async Pipeline (Week 3)

- [ ] `SongIdentityProvider` with version marker normalization
- [ ] `NeverRankedRestriction` using osu! API search
- [ ] `UniqueArtistTitleRestriction`
- [ ] `RuleValidationService` daemon
- [ ] `rejection_reason` field on Request model
- [ ] Phase 1/Phase 2 split in request submission flow
- [ ] Integration tests for async validation
- [ ] Song identity normalization tests

### Phase 4: API + Schema Updates (Week 4)

- [ ] OpenAPI schema updates for new restriction types
- [ ] `rejection_reason` in Request schema
- [ ] Rule version field on QueueRestriction
- [ ] Frontend: display rejection reason in request list
- [ ] Performance benchmarks
- [ ] Documentation for queue owners (rule authoring guide)

---

## 20. Design Principles

These principles guide all implementation decisions:

1. **Open/Closed Principle**: New rule types are added by creating new files — no modifications to existing code.
2. **Dependency Inversion**: Validators depend on abstractions (`ExecutionContext`, `MetadataProvider`) — not concrete implementations.
3. **Single Responsibility**: Each validator handles exactly one rule. Composite rules are handled by the evaluator, not individual validators.
4. **Fail-Open for External Services**: Tier 3 validators never block legitimate submissions when osu! API is unavailable.
5. **Configuration Over Code**: Rule logic is expressed in JSON config, not hardcoded in validators.
6. **Type Safety**: Pydantic schemas validate all configs at API time. Expression trees are typed.
7. **Testability**: Each validator is independently testable with mocked `ExecutionContext`. No global state.
