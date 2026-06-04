# Testing Graveboards Backend

This project needs a layered test suite. Keep most tests fast and isolated, then add a smaller number of infrastructure-backed tests for Connexion, SQLAlchemy CTEs, Redis, daemon services, and osu API behavior.

## Running Tests

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Run only the fast suite:

```bash
pytest -m unit
```

Run infrastructure-backed tests once fixtures exist:

```bash
pytest -m integration
```

## Test Layers

`unit`: Pure functions and small classes. No Redis, Postgres, network, app lifespan, or osu credentials. Good targets include search compression, search data-structure validation, URI parsing, validators, security helpers, shallow schema mutation, and error factories.

`integration`: Real local dependencies with disposable state. Good targets include SQLAlchemy CRUD, search CTE generation/results against seeded data, Redis models/decorators, beatmap manager filesystem behavior, and daemon service coordination.

`e2e`: Connexion routing with an ASGI client. These should verify that OpenAPI parameter parsing, validators, security handlers, error handlers, middleware, and endpoint functions work together. Avoid the app lifespan until you have explicit test fixtures for Redis/Postgres.

## Recommended Fixtures

Create small fixture modules as the suite grows:

- `tests/fixtures/spec.py`: minimal OpenAPI schema fragments for parser, validator, and shallow-schema tests.
- `tests/fixtures/search.py`: seeded beatmap/beatmapset/queue/request rows that prove CTE ranking and relationship scoring.
- `tests/fixtures/osu.py`: fake osu API responses and an `httpx.MockTransport` client.
- `tests/fixtures/redis.py`: Redis DB 15 cleanup before and after each integration test.
- `tests/fixtures/db.py`: test database creation, schema reset, transaction rollback, and factories for model rows.

## Connexion-Specific Strategy

Test Connexion behavior at two levels:

- Unit-test custom patches directly, like `OpenAPIURIParserPatched`, with minimal parameter definitions.
- E2E-test a tiny request through the Connexion app when you need to prove routing, OpenAPI validation, auth injection, or error handling.

Do not boot the real lifespan for parser and validator tests. The lifespan currently initializes Redis, Postgres, setup data, and the daemon, which makes simple request tests slow and brittle.

## What To Add Next

Start with focused tests for the riskiest contracts:

1. Search compression rejects malformed/truncated query payloads and round-trips representative query dictionaries.
2. Search schemas validate every supported scope, sorting option, condition operator, field weight, and pattern multiplier.
3. Search CTE integration tests seed a tiny graph and assert result ordering and scores for specific relationship cases.
4. Dynamic shallow schema tests assert that recursive shallow refs are expanded, cycles are dropped, and include recursion becomes the disabled boolean schema.
5. Security tests cover JWT expiry/signature failures, API-key hashing/validation, role/ownership decorators, and regex safety timeouts.
6. Daemon service tests cover start/stop idempotency, retry/backoff behavior, cancellation, and service supervisor failure handling.
