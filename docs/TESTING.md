# Testing Graveboards Backend

This project has a layered test suite with unit, integration, and e2e tests. Keep most tests fast and isolated, then add a smaller number of infrastructure-backed tests for PostgreSQL, Redis, daemon services, and osu! API behavior.

## Running Tests

```bash
source .venv/bin/activate
pytest
```

Run only unit tests:

```bash
pytest -m unit
```

Run integration tests (PostgreSQL/Redis required):

```bash
pytest -m integration
```

Run e2e tests:

```bash
pytest -m e2e
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Test Layers

`unit`: Pure functions and small classes. No Redis, Postgres, network, app lifespan, or osu credentials. Good targets include JWT, backoff strategies, security regex validation, database utility functions, Redis models/decorators, and search compression.

`integration`: Real local dependencies with disposable state. Good targets include SQLAlchemy CRUD operations, Redis rate limiting/caching/locking, daemon service coordination, and search CTE generation/results against seeded data.

`e2e`: Connexion routing with an ASGI client. These verify that OpenAPI parameter parsing, validators, security handlers, error handlers, middleware, and endpoint functions work together.

## Test Markers

- `unit`: Fast unit tests (default when running `pytest`)
- `integration`: Tests requiring PostgreSQL and Redis
- `e2e`: End-to-end tests with full application lifecycle
- `security`: Security-focused tests (JWT, API keys, regex protection)
- `slow`: Tests that take longer to execute
- `search`: Search-related tests

## Test Factories

Located in `tests/factories/`:

- `models.py`: `UserFactory`, `ProfileFactory`, `QueueFactory`, `RequestFactory`, schema factories
- `users.py` (planned): User/Profile factories based on `users/mania/` and `users/fruits/` osu! fixtures
- `scores.py` (planned): Score factory based on `scores/best/`, `scores/firsts/`, `scores/recent/` osu! fixtures
- `beatmaps.py` (planned): Beatmap factory based on `beatmaps/` osu! fixtures
- `beatmapsets.py` (planned): Beatmapset factory based on `beatmapsets/` osu! fixtures
- `queues.py` (planned): Queue factory extensions
- `requests.py` (planned): Request factory extensions

## Osu! Fixture Data

Fixture loader functions are in `tests/fixtures/osu/__init__.py`:

- `load_beatmap_fixture(beatmap_id)` — single beatmap data with embedded beatmapset
- `load_beatmapset_fixture(beatmapset_id)` — full beatmapset with nested beatmaps array
- `load_user_fixture(user_id, ruleset)` — user profile with statistics, kudosu, etc.
- `load_scores_fixture(user_id, score_type)` — best/firsts/recent scores array
- `load_beatmap_scores_fixture(beatmap_id)` — paginated scores for a beatmap
- `load_beatmap_attributes_fixture(beatmap_id, mods)` — star_rating under mods

### Available Fixtures

| Category | Count | Directory |
|----------|-------|-----------|
| Beatmaps | 47 | `tests/fixtures/osu/beatmaps/` |
| Beatmapsets | 32 | `tests/fixtures/osu/beatmapsets/` |
| Users — Mania | 28 | `tests/fixtures/osu/users/mania/` |
| Users — Fruits | 28 | `tests/fixtures/osu/users/fruits/` |
| Scores — Best | 17 | `tests/fixtures/osu/scores/best/` |
| Scores — Recent | 14 | `tests/fixtures/osu/scores/recent/` |
| Scores — Firsts | 17 | `tests/fixtures/osu/scores/firsts/` |
| Beatmap Scores | 7 | `tests/fixtures/osu/beatmap_scores/` |
| Beatmap Attributes | 21 | `tests/fixtures/osu/beatmap_attributes/` |
| **Total** | **214** | |

### Key Fixture Patterns

**Score ranks:** `XH`, `X`, `SH`, `S`, `A`, `B`, `D`
**Score types:** `score_best_osu`, `score_osu`, `solo_score`
**Mods:** `HD`, `DT`, `HR`, `NC`, `FL`, `PF`, `HT`, `SO`, `RX`, `TD`, `NF`, `EZ`
**Beatmap modes:** `osu` (0), `taiko` (1), `fruits` (2), `mania` (3)
**Beatmap status:** `graveyard` (-2), `ranked` (1), `loved` (4)

## Existing Tests

### Unit Tests

#### Security
- **JWT** (`tests/unit/security/test_jwt.py`): Token generation, encoding, decoding, validation, expiration handling
- **Regex** (`tests/unit/security/test_regex.py`): ReDoS timeout protection, valid/invalid regex compilation
- **API Keys** (`tests/unit/security/test_api_key.py`): Hashing, validation, role/ownership decorators (planned)

#### Database
- **Utils** (`tests/unit/database/test_utils.py`): Type extraction, validation, filter condition construction
- **Model Serialization** (`tests/unit/database/test_model_serialization.py`): Serialize/deserialize models to/from JSON (planned)
- **CRUD Input Logic** (`tests/unit/database/test_crud_input_logic.py`): Input validation for CRUD operations (planned)

#### Daemon
- **Backoff** (`tests/unit/daemon/test_backoff.py`): Constant, linear, and exponential backoff strategies, state transitions, reset functionality
- **Retry Policy** (`tests/unit/daemon/test_retry_policy.py`): Retry policies (planned)
- **Service** (`tests/unit/daemon/test_service.py`): Daemon service (planned)

#### Redis
- **Pool** (`tests/unit/redis/test_pool.py`): Connection pool initialization and state
- **Cache** (`tests/unit/redis/test_cache.py`): Set/get operations with TTL
- **Rate Limit** (`tests/unit/redis/test_rate_limit.py`): Rate limiting logic
- **Lock** (`tests/unit/redis/test_lock.py`): Distributed locking
- **Decorators** (`tests/unit/redis/test_decorators.py`): Cached, rate_limited, locked decorators
- **Rate Limit Decorator** (`tests/unit/redis/test_rate_limit_decorator.py`): Rate limit decorator behavior (planned)
- **Namespace Keys** (`tests/unit/redis/test_namespace_keys.py`): Redis namespace key generation (planned)
- **Models Serialization** (`tests/unit/redis/test_models_serialization.py`): Redis model serialization (planned)

#### Search
- **Compression** (`tests/unit/search/test_compression.py`): Query compress/decompress round-trip, error handling
- **Datastructures** (`tests/unit/search/test_datastructures.py`): Search data structures (planned)
- **Engine Validation** (`tests/unit/search/test_search_engine_validation.py`): Search engine input validation (planned)

#### Patches
- **URI Parsing** (`tests/unit/patches/test_uri_parsing.py`): DeepObject array resolution, coercion of booleans/JSON
- **Include Validator** (`tests/unit/patches/test_include_validator.py`): Include parameter validation (planned)
- **Filters Validator** (`tests/unit/patches/test_filters_validator.py`): Filter parameter validation (planned)
- **Sorting Validator** (`tests/unit/patches/test_sorting_validator.py`): Sorting parameter validation (planned)
- **Parameter Validator** (`tests/unit/patches/test_parameter_validator.py`): Parameter validation (planned)

#### Spec
- **Load Spec** (`tests/unit/spec/test_load_spec.py`): OpenAPI spec loading (planned)
- **Schema Resolution** (`tests/unit/spec/test_schema_resolution.py`): Schema resolution (planned)
- **Shallow Schema** (`tests/unit/spec/test_shallow_schema.py`): Shallow schema operations (planned)

#### Beatmaps
- **Manager** (`tests/unit/beatmaps/test_manager.py`): Beatmap archival/versioning (planned)

#### Osu! API Client
- **Client** (`tests/unit/osu_api/test_client.py`): Osu! API client methods — httpx.MockTransport with fixture data (planned)

### Integration Tests

#### API Routes
- **Auth** (`tests/integration/api/test_auth_routes.py`): OAuth login, token exchange, JWT issuance (planned)
- **Beatmaps** (`tests/integration/api/test_beatmaps_routes.py`): Beatmap CRUD, snapshots, tags (planned)
- **Queues** (`tests/integration/api/test_queues_routes.py`): Queue CRUD, visibility, managers (planned)
- **Requests** (`tests/integration/api/test_requests_routes.py`): Request CRUD, task management (planned)
- **Search** (`tests/integration/api/test_search_routes.py`): Full-text search, compression, includes (planned)
- **Error Handlers** (`tests/integration/api/test_error_handlers.py`): API error handling (planned)

#### Search
- **Engine Results** (`tests/integration/search/test_search_engine_results.py`): Full search queries against seeded data (planned)
- **Filtering CTEs** (`tests/integration/search/test_filtering_ctes.py`): Star rating, ranked, IDs filters (planned)
- **Sorting CTEs** (`tests/integration/search/test_sorting_ctes.py`): Title, difficulty, playcount sorting (planned)
- **Terms Scoring** (`tests/integration/search/test_search_terms_scoring.py`): Title/artist/tag priority (planned)
- **Terms Filtering** (`tests/integration/search/test_search_terms_filtering.py`): Substring/partial matching (planned)

#### Database
- **CRUD** (`tests/integration/database/test_crud.py`): CRUD operations with seeded data (planned)
- **Transactions** (`tests/integration/database/test_transactions.py`): Rollback isolation, concurrent access (planned)
- **Model Constraints** (`tests/integration/database/test_models_constraints.py`): Unique/FK/check constraints (planned)

#### Redis
- **Cache Integration** (`tests/integration/redis/test_cache_integration.py`): Cache behavior with real Redis (planned)
- **Rate Limit Integration** (`tests/integration/redis/test_rate_limit_integration.py`): Rate limiting with real Redis (planned)

#### Daemon
- **Daemon Services** (`tests/integration/daemon/test_daemon_services_integration.py`): Background service coordination (planned)

### E2E Tests

- **Smoke** (`tests/e2e/test_smoke.py`): Critical user flows with full app lifecycle (planned)

## Recommended Fixtures

- `tests/fixtures/spec.py`: OpenAPI schema fragments for parser/validator tests
- `tests/fixtures/search.py`: Seeded beatmap/beatmapset/queue/request rows for CTE tests
- `tests/fixtures/osu/`: Real osu! API responses for mock-based testing (214 files)
- `tests/fixtures/redis.py`: Redis DB cleanup before/after integration tests
- `tests/fixtures/db.py`: Test database setup, transaction rollback, model factories

---

# Test Implementation Plan

## Phase 1 — Osu! API Client Tests (Unit)
**File:** `tests/unit/osu_api/test_client.py`

Test all 8 `OsuAPIClient` methods by mocking httpx responses with real fixture data. Use `httpx.MockTransport` or `unittest.mock.patch`.

| Test | Fixture Source | Verifies |
|------|---------------|----------|
| `test_get_beatmap_parses_response` | `beatmaps/beatmap_116383.json` | Beatmap fields, embedded beatmapset, failtimes, max_combo |
| `test_get_beatmap_handles_404` | — | Raises appropriate error for missing beatmap |
| `test_get_beatmapset_parses_response` | `beatmapsets/beatmapset_22525.json` | Nested beatmaps array, covers (8 variants), tags, description |
| `test_get_user_parses_response` | `users/mania/user_7695647_mania.json` | Statistics (pp, rank, accuracy, grade_counts, level), kudosu, monthly_playcounts |
| `test_get_user_scores_best` | `scores/best/scores_2666342_best.json` | Score array, pp weighting, mod arrays, nested beatmap/beatmapset/user |
| `test_get_user_scores_recent` | `scores/recent/scores_6735738_recent.json` | `type` differentiation (`solo_score` vs `score_best_osu`), null pp |
| `test_get_user_scores_firsts` | `scores/firsts/scores_8558031_firsts.json` | SH/XH ranks, perfect flag, high pp values |
| `test_get_beatmap_scores` | `beatmap_scores/beatmap_scores_32781.json` | `score_count`, paginated scores, user team/cover data |
| `test_get_beatmap_attributes` | `beatmap_attributes/beatmap_attrs_87793_mods1.json` | `star_rating` under HD mod, max_combo |
| `test_get_beatmap_attributes_all_mods` | All 21 attr fixtures | Star rating increases with harder mods |
| `test_get_tags` | — | Parse beatmap/beatmapset tag lists |
| `test_get_rankings` | — | Parse ranking results by ruleset/mode |

## Phase 2 — Factory Implementation
**Files:** `tests/factories/scores.py`, `users.py`, `beatmaps.py`, `beatmapsets.py`

Build factories using real fixture data. These are prerequisites for all integration tests.

| Factory | Fixture Basis | Key Fields |
|---------|--------------|------------|
| `ScoreFactory` | `scores/best/scores_2666342_best.json` | accuracy, pp, max_combo, mods array, statistics dict, beatmap_id, user_id |
| `UserFactory` (extended) | `users/mania/user_7695647_mania.json` | statistics object, country, kudosu, grade_counts |
| `BeatmapFactory` | `beatmaps/beatmap_116383.json` | difficulty_rating, bpm, ar/cs/drain, counts, max_combo, checksum |
| `BeatmapsetFactory` | `beatmapsets/beatmapset_22525.json` | title, artist, status, favourite_count, bpm, tags, covers |

## Phase 3 — Integration API Route Tests
**Files:** `tests/integration/api/test_auth_routes.py`, `test_beatmaps_routes.py`, `test_queues_routes.py`, `test_requests_routes.py`, `test_search_routes.py`

Use `db_transaction` fixture for DB isolation and real Connexion ASGI client.

| Route Tests | What to Cover |
|------------|---------------|
| Auth | OAuth login flow start, token exchange, JWT issuance, token validation, invalid code error |
| Beatmaps | List/search (filters, sorting, pagination), get by ID, snapshot listing, tags, beatmap listings |
| Queues | Create/list/get/update, visibility (public/private), manager assignment |
| Requests | Create/list/get/update, task management, status transitions |
| Search | Full-text search across beatmaps/beatmapsets, query compression round-trip, include params |

## Phase 4 — Search Integration Tests
**Files:** `tests/integration/search/test_search_engine_results.py`, `test_filtering_ctes.py`, `test_sorting_ctes.py`, `test_search_terms_scoring.py`, `test_search_terms_filtering.py`

Seed test data from beatmap fixtures, verify CTE-based search behavior.

| Test | What It Covers |
|------|---------------|
| Engine Results | Full search queries against seeded beatmap data, result ordering, pagination |
| Filtering CTEs | Star rating, ranked, IDs, multi-field filters |
| Sorting CTEs | Title, difficulty_rating, playcount, bpm; asc/desc |
| Terms Scoring | Title match priority, artist, tags, partial matching, multi-term AND/OR |
| Terms Filtering | Filter by title substring, artist, tags, genre, language |

## Phase 5 — Database Integration Tests
**Files:** `tests/integration/database/test_crud.py`, `test_transactions.py`, `test_models_constraints.py`

| Test | What It Covers |
|------|---------------|
| CRUD | Create/read/update/delete for User, Profile, Beatmap, Beatmapset, Queue, Request |
| Transactions | Rollback isolation, concurrent access, transaction conflict handling |
| Model Constraints | Unique constraints, FK cascades, NOT NULL, check constraints, JSONB validation |

## Phase 6 — E2E Smoke Tests
**File:** `tests/e2e/test_smoke.py`

Full Connexion app with ASGI client:
- Beatmap search → result → beatmap detail
- User search → user profile
- Queue creation → request submission → request listing

## Phase 7 — Remaining Unit Tests
Fill in stub unit test files:

| File | What It Covers |
|------|---------------|
| `test_model_serialization.py` | Serialize/deserialize models to/from JSON |
| `test_crud_input_logic.py` | Input validation for CRUD operations |
| `test_rate_limit_decorator.py` | Rate limit decorator behavior |
| `test_namespace_keys.py` | Redis namespace key generation |
| `test_models_serialization.py` | Redis model serialization |
| `test_backoff.py`, `test_retry_policy.py`, `test_service.py` | Daemon service tests |
| `test_schema_resolution.py`, `test_shallow_schema.py`, `test_load_spec.py` | OpenAPI spec tests |
| `test_api_key.py`, `test_regex.py` | Security tests |
| `test_include_validator.py`, `test_filters_validator.py`, `test_sorting_validator.py`, `test_parameter_validator.py` | Parameter validator tests |
| `test_datastructures.py`, `test_search_engine_validation.py` | Search tests |
| `test_beatmap_manager.py` | Beatmap archival/versioning |

## Priority Order

| Priority | Phase | Rationale |
|----------|-------|-----------|
| **P0** | Phase 1 | `test_client.py` is explicitly empty; osu! API integration is core; 214 fixtures ready |
| **P0** | Phase 2 | Factories are prerequisite for all integration tests |
| **P1** | Phase 3 | API route tests are highest-value; verify full request-response chain |
| **P1** | Phase 4 | Search is most complex feature; CTE/logic bugs caught early |
| **P2** | Phase 5 | DB tests validate data integrity and model behavior |
| **P2** | Phase 6 | E2E tests validate critical user flows |
| **P3** | Phase 7 | Remaining unit tests fill gaps in utility code coverage |

---

# Execution Log

Track progress implementing the test plan above.

## Phase 1 — Osu! API Client Tests (Unit)
- [ ] `test_client.py` — all 12 tests implemented

## Phase 2 — Factory Implementation
- [ ] `tests/factories/scores.py` — ScoreFactory
- [ ] `tests/factories/users.py` — UserFactory extended
- [ ] `tests/factories/beatmaps.py` — BeatmapFactory
- [ ] `tests/factories/beatmapsets.py` — BeatmapsetFactory

## Phase 3 — Integration API Route Tests
- [ ] `tests/integration/api/test_auth_routes.py`
- [ ] `tests/integration/api/test_beatmaps_routes.py`
- [ ] `tests/integration/api/test_queues_routes.py`
- [ ] `tests/integration/api/test_requests_routes.py`
- [ ] `tests/integration/api/test_search_routes.py`

## Phase 4 — Search Integration Tests
- [ ] `tests/integration/search/test_search_engine_results.py`
- [ ] `tests/integration/search/test_filtering_ctes.py`
- [ ] `tests/integration/search/test_sorting_ctes.py`
- [ ] `tests/integration/search/test_search_terms_scoring.py`
- [ ] `tests/integration/search/test_search_terms_filtering.py`

## Phase 5 — Database Integration Tests
- [ ] `tests/integration/database/test_crud.py`
- [ ] `tests/integration/database/test_transactions.py`
- [ ] `tests/integration/database/test_models_constraints.py`

## Phase 6 — E2E Smoke Tests
- [ ] `tests/e2e/test_smoke.py`

## Phase 7 — Remaining Unit Tests
- [ ] `tests/unit/database/test_model_serialization.py`
- [ ] `tests/unit/database/test_crud_input_logic.py`
- [ ] `tests/unit/redis/test_rate_limit_decorator.py`
- [ ] `tests/unit/redis/test_namespace_keys.py`
- [ ] `tests/unit/redis/test_models_serialization.py`
- [ ] `tests/unit/daemon/test_backoff.py`
- [ ] `tests/unit/daemon/test_retry_policy.py`
- [ ] `tests/unit/daemon/test_service.py`
- [ ] `tests/unit/spec/test_schema_resolution.py`
- [ ] `tests/unit/spec/test_shallow_schema.py`
- [ ] `tests/unit/spec/test_load_spec.py`
- [ ] `tests/unit/security/test_api_key.py`
- [ ] `tests/unit/security/test_regex.py`
- [ ] `tests/unit/patches/test_include_validator.py`
- [ ] `tests/unit/patches/test_filters_validator.py`
- [ ] `tests/unit/patches/test_sorting_validator.py`
- [ ] `tests/unit/patches/test_parameter_validator.py`
- [ ] `tests/unit/search/test_datastructures.py`
- [ ] `tests/unit/search/test_search_engine_validation.py`
- [ ] `tests/unit/beatmaps/test_manager.py`
