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

Located in `tests/factories/models.py`:

- `UserFactory`: Creates test users with profile
- `ProfileFactory`: Creates test profiles
- `QueueFactory`: Creates test queues
- `RequestFactory`: Creates test requests
- `ProfileSchemaFactory`: Schema factories for validation tests
- `QueueSchemaFactory`: Schema factories for validation tests
- `RequestSchemaFactory`: Schema factories for validation tests

## Unit Tests

### Security
- **JWT** (`tests/unit/security/test_jwt.py`): Token generation, encoding, decoding, validation, expiration handling
- **Regex** (`tests/unit/security/test_regex.py`): ReDoS timeout protection, valid/invalid regex compilation
- **API Keys**: Hashing, validation, role/ownership decorators (planned)

### Database
- **Utils** (`tests/unit/database/test_utils.py`): Type extraction, validation, filter condition construction

### Daemon
- **Backoff** (`tests/unit/daemon/test_backoff.py`): Constant, linear, and exponential backoff strategies, state transitions, reset functionality

### Redis
- **Pool** (`tests/unit/redis/test_pool.py`): Connection pool initialization and state
- **Cache** (`tests/unit/redis/test_cache.py`): Set/get operations with TTL
- **Rate Limit** (`tests/unit/redis/test_rate_limit.py`): Rate limiting logic
- **Lock** (`tests/unit/redis/test_lock.py`): Distributed locking
- **Decorators** (`tests/unit/redis/test_decorators.py`): Cached, rate_limited, locked decorators

## Recommended Fixtures

- `tests/fixtures/spec.py`: OpenAPI schema fragments for parser/validator tests
- `tests/fixtures/search.py`: Seeded beatmap/beatmapset/queue/request rows for CTE tests
- `tests/fixtures/osu.py`: Fake osu API responses and httpx.MockTransport
- `tests/fixtures/redis.py`: Redis DB cleanup before/after integration tests
- `tests/fixtures/db.py`: Test database setup, transaction rollback, model factories

## What To Add Next

1. Integration tests for PostgreSQL CRUD operations with `db_transaction` fixture
2. Integration tests for Redis rate limiting, caching, and locking
3. API integration tests for main endpoints (auth, search, beatmaps)
4. E2E smoke tests for critical user flows
5. Expand factory data with valid test data from osu! API
