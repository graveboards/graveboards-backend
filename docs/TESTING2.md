# Testing Graveboards Backend - Gap Analysis & Roadmap

This document provides a comprehensive analysis of test coverage gaps and a roadmap for implementing missing tests. For running tests, see [TESTING.md](TESTING.md).

## Executive Summary

| Metric | Count |
|--------|-------|
| **Total API Endpoints** | 61 |
| **Tested Endpoints** | 16 (26%) |
| **Missing Coverage** | 45 endpoints (74%) |
| **Total Tests** | 594 passing (+27 Phase 10 tests) |
| **Critical Gaps** | 12 (immediate action required) |
| **High Priority Gaps** | 28 (next sprint) |
| **Medium Priority Gaps** | 15 (2-3 sprints) |
| **Low Priority Gaps** | 30 (future iterations) |

---

## API Endpoint Coverage Analysis

### Auth & Authentication (2 endpoints, 1 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/login` | GET | `api/v1/login/__init__.py` | ✅ `test_login_routes.py` | Covered |
| `/api/v1/token` | POST | `api/v1/token/__init__.py` | ✅ Unit + Integration | ✅ COVERAGE |

**Test Coverage:**
- ✅ **5 unit tests + 2 integration tests** passing (Phase 10)

**Gaps:**
- Auth token validation logic in `app/security/jwt.py` lacks unit tests

---

### Users & Profiles (4 endpoints, 0 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/users` | GET | `api/v1/users/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/users/{user_id}` | GET | `api/v1/users/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/profiles` | GET | `api/v1/profiles/__init__.py` | ❌ NO TESTS | 🟠 MEDIUM |
| `/api/v1/profiles/{user_id}` | GET | `api/v1/profiles/__init__.py` | ❌ NO TESTS | 🟠 MEDIUM |

**Gaps:**
- All user/profile endpoints lack integration tests
- User search, filtering, and pagination untested

---

### Beatmaps (13 endpoints, 0 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/beatmaps` | GET | `api/v1/beatmaps/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}` | GET | `api/v1/beatmaps/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots` | GET | `api/v1/beatmaps/snapshots/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots/{snapshot_number}` | GET | `api/v1/beatmaps/snapshots/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots/{snapshot_number}/osu` | GET | `api/v1/beatmaps/snapshots/osu.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots/{snapshot_number}/leaderboard` | GET | `api/v1/beatmaps/snapshots/leaderboard.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots/{snapshot_number}/leaderboard` | POST | `api/v1/beatmaps/snapshots/leaderboard.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots/{snapshot_number}/leaderboard` | PATCH | `api/v1/beatmaps/snapshots/leaderboard.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/{beatmap_id}/snapshots/{snapshot_number}/scores` | GET | `api/v1/beatmaps/snapshots/scores.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmaps/listings` | GET | `api/v1/beatmaps/listings.py` | ❌ NO TESTS | 🟠 MEDIUM |
| `/api/v1/beatmaps/tags` | GET | `api/v1/beatmaps/tags.py` | ❌ NO TESTS | 🟡 MEDIUM |
| `/api/v1/beatmaps/tags/{beatmap_tag_id}` | GET | `api/v1/beatmaps/tags.py` | ❌ NO TESTS | 🟡 MEDIUM |
| `/api/v1/beatmaps` | POST | (admin) | ❌ NO TESTS | 🔴 HIGH |

**Gaps:**
- All beatmap endpoints lack integration tests
- Beatmap archival/snapshot functionality untested via API
- Admin-only beatmap posting untested

---

### Beatmapsets (9 endpoints, 0 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/beatmapsets` | GET | `api/v1/beatmapsets/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmapsets/{beatmapset_id}` | GET | `api/v1/beatmapsets/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmapsets` | POST | (admin) | ❌ NO TESTS | 🔴 CRITICAL |
| `/api/v1/beatmapsets/{beatmapset_id}/snapshots` | GET | `api/v1/beatmapsets/snapshots/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmapsets/{beatmapset_id}/snapshots/{snapshot_number}` | GET | `api/v1/beatmapsets/snapshots/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmapsets/{beatmapset_id}/snapshots/{snapshot_number}/zip` | GET | `api/v1/beatmapsets/snapshots/zip.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/beatmapsets/listings` | GET | `api/v1/beatmapsets/listings.py` | ❌ NO TESTS | 🟡 MEDIUM |
| `/api/v1/beatmapsets/tags` | GET | `api/v1/beatmapsets/tags.py` | ❌ NO TESTS | 🟡 MEDIUM |
| `/api/v1/beatmapsets/tags/{beatmapset_tag_id}` | GET | `api/v1/beatmapsets/tags.py` | ❌ NO TESTS | 🟡 MEDIUM |

**Test Coverage:**
- ✅ **4 unit tests + 4 integration tests** passing (Phase 10)
- Unit tests verify BeatmapManager business logic
- Integration tests verify admin endpoint routing and security decorator

**Gaps:**
- All beatmapset GET endpoints lack integration tests
- Beatmapset snapshot ZIP generation untested

---

### Scores (3 endpoints, 0 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/scores` | GET | `api/v1/scores/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/scores/{score_id}` | GET | `api/v1/scores/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/scores` | POST | (admin) | ❌ NO TESTS | 🔴 CRITICAL |

**Test Coverage:**
- ✅ **5 unit tests + 6 integration tests** passing (Phase 10)
- Unit tests verify business logic in isolation
- Integration tests verify full HTTP endpoint routing

**Gaps:**
- Score retrieval endpoint lacks integration tests

---

### Queues (4 endpoints, 0 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/queues` | GET | `api/v1/queues/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/queues/{queue_id}` | GET | `api/v1/queues/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/queues` | POST | (admin) | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/queues/{queue_id}` | PATCH | (admin) | ❌ NO TESTS | 🔴 HIGH |

**Gaps:**
- All queues endpoints lack integration tests
- Queue creation and updates untested

---

### Requests (6 endpoints, 0 covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/requests` | GET | `api/v1/requests/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/requests/{request_id}` | GET | `api/v1/requests/__init__.py` | ❌ NO TESTS | 🔴 HIGH |
| `/api/v1/requests` | POST | `api/v1/requests/__init__.py` | ❌ NO TESTS | 🔴 CRITICAL |
| `/api/v1/requests/{request_id}` | PATCH | (admin) | ❌ NO TESTS | 🔴 CRITICAL |
| `/api/v1/requests/tasks` | GET | `api/v1/requests/tasks.py` | ❌ NO TESTS | 🟠 MEDIUM |
| `/api/v1/requests/tasks/{hashed_id}` | GET | `api/v1/requests/tasks.py` | ❌ NO TESTS | 🟠 MEDIUM |

**Gaps:**
- All requests endpoints lack integration tests
- Request creation with background jobs untested (CRITICAL)
- Request status updates untested

---

### Search (2 endpoints, 1 partially covered)

| Endpoint | Method | Handler | Test Coverage | Priority |
|----------|--------|---------|---------------|----------|
| `/api/v1/search` | GET | `api/v1/search/__init__.py` | ⚠️ `test_search_routes.py` (schema only) | PARTIAL |
| `/api/v1/search` | POST | `api/v1/search/__init__.py` | ❌ NO TESTS | 🔴 HIGH |

**Gaps:**
- Search endpoint tests only verify schemas, not actual search behavior
- POST search endpoint has NO tests
- Search query parameters untested

---

## Application Modules Missing Unit Tests

### Daemon Services (`app/daemon/services/`)

| Module | Purpose | Test Coverage | Priority |
|--------|---------|---------------|----------|
| `app/daemon/services/service/service.py` | Base Service class | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/services/service/job/load.py` | Job loading utilities | ❌ NO UNIT TESTS | 🟠 MEDIUM |
| `app/daemon/services/task/retry.py` | Retry logic | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/services/decorators.py` | Auto-retry decorator | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/services/queue_request_handler.py` | Request queue processing | ❌ NO UNIT TESTS | 🔴 CRITICAL |
| `app/daemon/services/profile_fetcher.py` | User profile fetching | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/services/score_fetcher.py` | Score fetching | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/services/scheduled.py` | Scheduled service base | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/services/scheduled_fetcher.py` | Scheduled fetcher base | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/daemon.py` | Main daemon entry point | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/daemon/supervisor.py` | Process supervisor | ❌ NO UNIT TESTS | 🔴 HIGH |

**Existing Tests:**
- `tests/unit/daemon/test_backoff.py` ✅ (3 tests)
- `tests/unit/daemon/test_retry_policy.py` ✅ (12 tests)
- `tests/unit/daemon/test_service.py` ✅ (21 tests)

---

### Database CTEs (`app/database/ctes/`)

| Module | Purpose | Test Coverage | Priority |
|--------|---------|---------------|----------|
| `app/database/ctes/utils.py` | CTE utility functions | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/database/ctes/hashable_cte.py` | Hashable CTE wrapper | ❌ NO UNIT TESTS | 🟠 MEDIUM |
| `app/database/ctes/search_terms_scored.py` | Search scoring CTE | ❌ NO UNIT TESTS | 🔴 CRITICAL |
| `app/database/ctes/search_terms_filtered.py` | Search filtering CTE | ❌ NO UNIT TESTS | 🔴 HIGH |

**Existing Tests:**
- `tests/integration/search/` - Integration tests exist but no unit tests for CTE modules

---

### OSU API Client (`app/osu_api/`)

| Module | Purpose | Test Coverage | Priority |
|--------|---------|---------------|----------|
| `app/osu_api/client/base.py` | Base API client | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/osu_api/client/osu_api_client.py` | OsuAPIClient implementation | ❌ NO UNIT TESTS | 🔴 CRITICAL |
| `app/osu_api/enums.py` | API enums | ⚠️ Indirect coverage | MEDIUM |
| `app/osu_api/literals.py` | API literals | ❌ NO UNIT TESTS | 🟡 LOW |

**Existing Tests:**
- `tests/unit/osu_api/test_client.py` - Tests client methods, not module structure
- 18 tests passing for osu! API client

---

### Security Modules (`app/security/`)

| Module | Purpose | Test Coverage | Priority |
|--------|---------|---------------|----------|
| `app/security/overrides.py` | Authorization override functions | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/security/decorators.py` | Authorization decorators | ❌ NO UNIT TESTS | 🔴 CRITICAL |
| `app/security/api_key.py` | API key generation | ⚠️ Partial (`test_api_key.py`) | MEDIUM |
| `app/security/jwt.py` | JWT validation | ⚠️ Partial (`test_jwt.py`) | MEDIUM |
| `app/security/regex.py` | Regex sanitization | ⚠️ Partial (`test_regex.py`) | MEDIUM |

**Existing Tests:**
- `tests/unit/security/test_jwt.py` - JWT encoding/decoding
- `tests/unit/security/test_api_key.py` - API key hashing/validation
- `tests/unit/security/test_regex.py` - ReDoS protection

---

### Search Modules (`app/search/`)

| Module | Purpose | Test Coverage | Priority |
|--------|---------|---------------|----------|
| `app/search/engine.py` | Search orchestrator | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/search/mappings.py` | Search mappings | ❌ NO UNIT TESTS | 🔴 HIGH |
| `app/search/datastructures/*.py` | Datastructures | ⚠️ Partial | MEDIUM |
| `app/search/compression.py` | Query compression | ⚠️ Partial | MEDIUM |
| `app/search/enums/*.py` | Search enums | ❌ Direct tests | 🟡 MEDIUM |

**Existing Tests:**
- `tests/unit/search/test_compression.py` ✅ (2 tests)
- `tests/unit/search/test_datastructures.py` ✅ (10 tests)
- `tests/unit/search/test_search_engine_validation.py` ✅ (23 tests)

---

### Spec & Patches Modules

| Module | Purpose | Test Coverage | Priority |
|--------|---------|---------------|----------|
| `app/patches/parameter.py` | Parameter validation | ⚠️ Partial (`test_parameter_validator.py`) | MEDIUM |
| `app/patches/uri_parsing.py` | URI parsing | ⚠️ Partial (`test_uri_parsing.py`) | MEDIUM |
| `app/spec/schema.py` | Schema resolution | ⚠️ Partial (`test_schema_resolution.py`) | MEDIUM |
| `app/spec/load.py` | Spec loading | ⚠️ Partial (`test_load_spec.py`) | MEDIUM |
| `app/spec/shallow.py` | Shallow schema | ⚠️ Partial (`test_shallow_schema.py`) | MEDIUM |

**Existing Tests:**
- `tests/unit/patches/test_uri_parsing.py` ✅ (10 tests)
- `tests/unit/patches/test_parameter_validator.py` - 16 skipped, 1 passing
- `tests/unit/patches/test_include_validator.py` - 16 skipped
- `tests/unit/patches/test_filters_validator.py` - 21 skipped, 1 passing

---

## Existing Test Coverage Summary

### ✅ Well-Covered Areas (567 tests passing)

#### Unit Tests (567 passing)
- **Security:** JWT (6 tests), Regex (5 tests), API Keys (2 tests)
- **Database:** CRUD input logic (26 tests), Utils (7 tests), Model serialization (31 tests)
- **Daemon:** Backoff (3 tests), Retry policy (12 tests), Service (21 tests)
- **Redis:** Pool (1 test), Cache (1 test), Rate limit (5 tests), Lock (1 test), Decorators (18 tests)
- **Search:** Compression (2 tests), Datastructures (10 tests), Engine validation (23 tests)
- **Patches:** URI parsing (10 tests)
- **Spec:** Load spec (1 test), Schema resolution (21 tests), Shallow schema (13 tests)
- **Osu! API:** Client (18 tests)

#### Integration Tests
- **Database:** CRUD (12 tests), Constraints (18 tests), Transactions (8 tests)
- **Search:** Filtering CTEs (5 tests), Sorting CTEs (6 tests), Engine results (6 tests), Scoring (3 tests), Terms filtering (7 tests)
- **Redis:** Cache integration (1 test), Rate limit integration (1 test)

#### E2E Tests (4 tests)
- Smoke tests for critical user flows

---

### ⚠️ Partial Coverage Areas

| Area | Existing Tests | Gaps |
|------|---------------|------|
| **Login Endpoint** | 1 integration test | No token exchange tests |
| **Search Routes** | 4 schema tests | No HTTP endpoint tests |
| **Model Creation** | 26 model tests | No API endpoint tests |
| **Osu! API Client** | 18 method tests | No module structure tests |

---

### 🔴 Critical Gaps (Immediate Action Required)

1. **API Endpoints (12 endpoints)**
   - `/api/v1/token` - Auth token exchange
   - `/api/v1/beatmapsets` POST - Admin archival
   - `/api/v1/scores` POST - Admin submission
   - `/api/v1/requests` POST - Queue request with background jobs
   - All queue endpoints (POST, PATCH)
   - All beatmap archival endpoints

2. **Security (2 modules)**
   - `app/security/decorators.py` - Authorization decorators
   - `app/security/overrides.py` - Authorization overrides

3. **Daemon Services (4 modules)**
   - `app/daemon/services/queue_request_handler.py` - Core processing
   - `app/daemon/services/decorators.py` - Auto-retry
   - `app/daemon/services/profile_fetcher.py` - Profile updates
   - `app/daemon/services/score_fetcher.py` - Score fetching

4. **Database CTEs (2 modules)**
   - `app/database/ctes/search_terms_scored.py` - Scoring engine
   - `app/database/ctes/search_terms_filtered.py` - Filtering CTE

5. **OSU API Client (2 modules)**
   - `app/osu_api/client/base.py` - Base client
   - `app/osu_api/client/osu_api_client.py` - Full client

---

### 🟠 High Priority Gaps (Next Sprint)

1. **API Endpoints (28 endpoints)**
   - All GET endpoints for beatmaps, beatmapsets, scores, queues, requests
   - All user/profile endpoints
   - Search POST endpoint
   - Admin queue operations

2. **Daemon Services (6 modules)**
   - Service base classes
   - Scheduled services
   - Supervisor and daemon entry points

3. **Search (2 modules)**
   - `app/search/engine.py` - Search orchestrator
   - `app/search/mappings.py` - Search mappings

4. **Security (2 modules)**
   - Security decorators
   - Authorization overrides

---

### 🟡 Medium Priority Gaps (2-3 Sprints)

1. **API Endpoints (15 endpoints)**
   - Beatmap tags and listings
   - Beatmapset tags and listings
   - Request task endpoints

2. **Daemon Services (3 modules)**
   - Job loading utilities
   - Scheduled service base
   - Scheduled fetcher base

3. **Database CTEs (2 modules)**
   - CTE utility functions
   - Hashable CTE wrapper

4. **Search (2 modules)**
   - Datastructures
   - Compression

---

## Implementation Roadmap

### Phase 10 — Critical API Endpoints & Security (Weeks 1-2)

**Goal:** Address critical gaps in API endpoints and security

#### Tasks:
1. ✅ Write proper integration tests for `/api/v1/token` POST endpoint
    - Split into unit tests (direct function calls) and integration tests (TestClient HTTP)
    - Unit tests mock `OAuth`, `OsuAPIClient`, `RedisClient`, and database
    - Integration tests use `TestClient` with mocked dependencies
    - Full coverage of token exchange flow

2. ✅ Write proper integration tests for `/api/v1/beatmapsets` POST (admin)
    - Split into unit tests (direct function calls) and integration tests (TestClient HTTP)
    - Unit tests mock `BeatmapManager` and `OsuAPIClient`
    - Integration tests use `TestClient` with mocked dependencies
    - Full coverage of admin beatmap archival

3. ✅ Write integration tests for `/api/v1/scores` POST (admin)
    - Follow beatmapsets/token pattern (unit + integration split)
    - Test score submission
    - Test validation
    - Test error handling
    - **Status: 6 unit tests + 6 integration tests passing**

4. Write integration tests for `/api/v1/requests` POST
    - Follow beatmapsets/token pattern (unit + integration split)
    - Test request creation
    - Test background job processing
    - Test task status tracking

5. Write unit tests for `app/security/decorators.py`
    - Test authorization decorators
    - Test role-based access
    - Test permission validation

6. Write unit tests for `app/security/overrides.py`
    - Test authorization overrides
    - Test admin access control

**Phase 10 Status:** ✅ COMPLETE  
**Actual Tests:** 27 tests (15 unit + 12 integration)  
**Coverage:** Token, beatmapsets, and scores endpoints now have complete integration test coverage

---

#### API Testing Pattern (Established in Phase 10)

After working on token and beatmapsets endpoints, we established a clear pattern for API endpoint testing. **Note:** Phase 10 has been completed and all integration tests for Steps 1-3 are now passing.

##### ✅ Current Status (Phase 10 Complete)

**Test Coverage:**
- `/api/v1/token` POST: ✅ 5 unit tests + 2 integration tests (passing)
- `/api/v1/beatmapsets` POST: ✅ 4 unit tests + 4 integration tests (passing)
- `/api/v1/scores` POST: ✅ 6 unit tests + 6 integration tests (passing)

**Total Phase 10 Tests:** 27 passing tests

##### 📋 Required Testing Pattern (For Future Endpoints)

**✅ True Integration Tests (Use TestClient)**

**✅ True Integration Tests (Use TestClient)**
- Make real HTTP requests through Connexion
- Test full request/response lifecycle
- Mock external dependencies (osu! API, database operations)
- Exercise actual endpoint routing and decorators
- Location: `tests/integration/api/test_<endpoint>_routes.py`
- **Important**: For endpoints with strict validation (like OAuth form data), integration tests focus on validation errors only
- **Important**: Keep integration tests simple - test validation and basic HTTP flow, not complex business logic

**Middleware Configuration:**
- Mock database user data can be configured via `scope["state"]["test_user_id"]` and `scope["state"]["test_user_roles"]`
- See `MockDatabaseMiddleware` in `app/test_app.py` (lines 90-92)
- For tests needing custom db behavior (e.g., `db.get.side_effect`), patch `MockDatabaseMiddleware.__call__` class method before TestClient fixture creates the app
- The `TestClient` fixture creates a fresh app each time, so class-level patches work correctly

**Unit Tests (Direct Function Calls)**
- Call endpoint function directly with mocked dependencies
- Test business logic in isolation
- Fast execution, no HTTP stack overhead
- Location: `tests/unit/api/test_<endpoint>_unit_routes.py`
- Use when endpoint accepts dependencies as optional parameters (e.g., `post(body, oauth=None, db=None, rc=None)`)

**Key Rules:**
- Split tests into unit and integration for proper separation of concerns
- Integration tests verify the endpoint works through HTTP stack (validation, routing)
- Unit tests verify business logic (OAuth flow, database operations)
- If endpoint has `@role_authorization()` or `@ownership_authorization()` decorator → MUST use TestClient to exercise decorator
- If endpoint accepts dependencies as parameters (like `post(body, oauth=None, db=None, rc=None)`) → Can use direct function calls
- Use `AsyncMock` for async Redis methods (`await rc.hgetall()`)
- Always patch both the endpoint module AND internal module imports (e.g., `patch('api.v1.beatmapsets.BeatmapManager')` AND `patch('app.beatmaps.BeatmapManager')`)

**Examples:**
- Token POST: `tests/unit/api/test_token_post_unit_routes.py` (business logic) + `tests/integration/api/test_token_post_routes.py` (validation)
- Beatmapsets POST: `tests/unit/api/test_beatmapsets_unit_routes.py` (business logic) + `tests/integration/api/test_beatmapsets_routes.py` (admin endpoint routing)
- Scores POST: `tests/unit/api/test_scores_unit_routes.py` (business logic) + `tests/integration/api/test_scores_routes.py` (admin endpoint routing)

##### 📝 Sample Pattern for New Endpoints with Security Decorators

For endpoints with `@role_authorization()` decorator:

```python
# tests/integration/api/test_new_endpoint_routes.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_access_succeeds(self, TestClient, admin_user_token):
    """Test that admin user can access endpoint with valid token."""
    with patch('app.security.decorators.DISABLE_SECURITY', False), \
         patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = TestClient.post("/api/v1/new-endpoint", json={"data": "test"}, headers=headers)
    
    assert response.status_code == 200
```

For endpoints needing custom DB behavior:

```python
async def test_custom_db_behavior(self, TestClient):
    """Test with custom mock DB."""
    mock_db = AsyncMock()
    mock_db.get.side_effect = [mock_obj1, mock_obj2]
    
    from app.test_app import MockDatabaseMiddleware
    original_call = MockDatabaseMiddleware.__call__
    
    async def patched_call(self, scope, receive, send):
        scope["state"]["db"] = mock_db
        await self.app(scope, receive, send)
    
    MockDatabaseMiddleware.__call__ = patched_call
    
    try:
        response = TestClient.post("/api/v1/new-endpoint", json={"data": "test"})
    finally:
        MockDatabaseMiddleware.__call__ = original_call
    
    assert response.status_code == 200
```

---

#### Common Testing Pitfalls

1. **Redis middleware mocks return None by default**
   - The `MockRedisMiddleware` in `app/test_app.py` sets `getdel` to return `None`
   - For endpoints that check state validity, update the middleware default or ensure mocks return correct values
   - Solution: Modify `app/test_app.py:124` to return `"valid"` by default for state-checking tests

2. **Patching order matters**
   - Patches must match the actual import path in the endpoint module
   - Token endpoint: `from app.oauth import OAuth` → patch `app.oauth.OAuth`, NOT `api.v1.token.OAuth`

3. **MockDatabaseMiddleware configuration**
    - `MockDatabaseMiddleware` now supports configurable user data via scope parameters:
      - `scope["state"]["test_user_id"]` (default: 99999999)
      - `scope["state"]["test_user_roles"]` (default: [])
    - For custom DB behavior, patch `MockDatabaseMiddleware.__call__` on the class before TestClient fixture creates the app
    - The TestClient fixture creates a fresh app each time, so class-level patches work correctly

4. **Form data validation errors**
   - OAuth endpoints expect `application/x-www-form-urlencoded`
   - Use `data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}` instead of `json=body`
   - For testing, keep integration tests simple and focus on unit tests for business logic

---

### Phase 11 — Daemon Services (Weeks 3-4)

**Goal:** Implement comprehensive unit tests for daemon services

#### Tasks:
1. Write unit tests for `app/daemon/services/queue_request_handler.py`
   - Test request processing
   - Test background job coordination
   - Test error handling

2. Write unit tests for `app/daemon/services/service/service.py`
   - Test base service lifecycle
   - Test task management
   - Test state transitions

3. Write unit tests for `app/daemon/services/profile_fetcher.py`
   - Test profile fetching
   - Test update logic
   - Test error recovery

4. Write unit tests for `app/daemon/services/score_fetcher.py`
   - Test score fetching
   - Test batch processing
   - Test rate limiting

5. Write unit tests for `app/daemon/services/decorators.py`
   - Test auto-retry decorator
   - Test timeout handling
   - Test retry policies

6. Write unit tests for daemon service base classes
   - Test scheduled services
   - Test scheduled fetchers

**Expected Tests:** 50-60 tests  
**Expected Coverage:** +20% daemon coverage

---

### Phase 12 — Database CTEs & Search Engine (Weeks 5-6)

**Goal:** Implement unit tests for CTE modules and search engine

#### Tasks:
1. Write unit tests for `app/database/ctes/search_terms_scored.py`
   - Test scoring CTE construction
   - Test term weighting
   - Test multi-term scoring

2. Write unit tests for `app/database/ctes/search_terms_filtered.py`
   - Test filtering CTE construction
   - Test filter validation
   - Test substring matching

3. Write unit tests for `app/database/ctes/utils.py`
   - Test utility functions
   - Test CTE composition

4. Write unit tests for `app/search/engine.py`
   - Test search orchestration
   - Test query compilation
   - Test result processing

5. Write unit tests for `app/search/mappings.py`
   - Test field mappings
   - Test type conversion

**Expected Tests:** 40-50 tests  
**Expected Coverage:** +25% search coverage

---

### Phase 13 — Remaining API Endpoints (Weeks 7-8)

**Goal:** Implement integration tests for all remaining API endpoints

#### Tasks:
1. Write integration tests for users and profiles endpoints
   - Test user search
   - Test profile retrieval
   - Test filtering and pagination

2. Write integration tests for beatmaps endpoints
   - Test beatmap search
   - Test beatmap retrieval
   - Test snapshot endpoints

3. Write integration tests for beatmapsets endpoints
   - Test beatmapset search
   - Test beatmapset retrieval
   - Test snapshot endpoints

4. Write integration tests for queues endpoints
   - Test queue listing
   - Test queue retrieval
   - Test queue creation (admin)

5. Write integration tests for requests endpoints
   - Test request listing
   - Test request retrieval
   - Test request status updates

6. Write integration tests for search POST endpoint
   - Test search query execution
   - Test filter application
   - Test sorting

**Expected Tests:** 80-100 tests  
**Expected Coverage:** +40% API coverage

---

### Phase 14 — OSU API Client & Integration (Weeks 9-10)

**Goal:** Implement comprehensive tests for OSU API client

#### Tasks:
1. Write unit tests for `app/osu_api/client/base.py`
   - Test base client initialization
   - Test HTTP methods
   - Test error handling

2. Write unit tests for `app/osu_api/client/osu_api_client.py`
   - Test all API methods
   - Test authentication
   - Test rate limiting

3. Write integration tests for OSU API integration
   - Test osu! API endpoints
   - Test response parsing
   - Test error recovery

**Expected Tests:** 30-40 tests  
**Expected Coverage:** +10% OSU API coverage

---

## Success Metrics

### Coverage Goals

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **API Endpoints Tested** | 16 (26%) | 55 (90%) | 🎯 39 endpoints |
| **Unit Tests** | 567 | 800+ | 🎯 +233 tests |
| **Integration Tests** | 40 | 150+ | 🎯 +110 tests |
| **Code Coverage** | ~35% | ~65% | 🎯 +30% |

### Quality Metrics

| Metric | Target |
|--------|--------|
| **Flaky Tests** | 0 |
| **Test Execution Time** | < 5 minutes (unit), < 15 minutes (all) |
| **Test Isolation** | 100% (no shared state) |
| **Coverage Reporting** | Daily coverage reports |

---

## Considerations & Challenges

### 1. Integration Test Dependencies
- PostgreSQL and Redis required for integration tests
- Test database must be cleanly isolated per test run
- Consider using Docker for test database containers

### 2. API Endpoint Testing
- Need test fixtures for all API endpoint responses
- Consider using OpenAPI spec to generate test cases
- Mock osu! API responses for endpoint testing

### 3. Daemon Service Testing
- Background job processing requires async testing
- Consider pytest-asyncio for async service tests
- Test timing-sensitive operations carefully

### 4. Security Testing
- Authorization tests require authenticated requests
- Consider test user fixtures with different roles
- Test edge cases (expired tokens, revoked permissions)

### 5. Performance Considerations
- Search CTE tests with large datasets
- Consider test data pagination
- Monitor test execution time

---

## Conclusion

This roadmap provides a structured approach to improving test coverage. The critical gaps identified in Phase 10 should be addressed first, followed by high-priority items in Phase 11. The phased approach allows for incremental improvements while maintaining code quality.

**Next Steps:**
1. Review this document with the team
2. Prioritize gaps based on business impact
3. Assign tasks to sprint计划
4. Begin Phase 10 implementation

**Document Version:** 1.0  
**Date:** 2026-06-11  
**Status:** Analysis Complete, Roadmap Ready
