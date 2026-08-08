# Graveboards Backend — Agent Instructions

## Test suite contract

### Fast feedback (the command you reach for first)
```
ENV=test uv run pytest -m unit -n auto --no-cov -q
```
Runs all unit tests in parallel, no coverage, under 10s. No DB/Redis needed.

### Full local suite
```
make test-all    # needs PG + Redis running locally
```
Runs everything except coverage in parallel.

### Coverage (slow; CI-only)
```
make test-cov
```
Runs unit + integration with coverage. Gate is a floor (70%), not a target.

### Lint / typecheck
```
make lint
make typecheck
```

### Docker (full CI parity)
```
make test-docker
```

## Rules for test authors

1. **Never add `--cov` to `addopts`.** Coverage is opt-in and lives in `make test-cov` only.

2. **Every new test file** placed under `tests/unit/`, `tests/integration/`, or `tests/e2e/` is auto-marked by directory. Do NOT rely on `item.keywords` — the auto-marker uses `get_closest_marker`.

3. **Shared test doubles** (`MockSession`, `MockLockCtx`, `mock_redis_client`) live in `tests/_helpers/mocks.py`. Do not redefine them inline.

4. **Helper modules** must NEVER be named `test_*`. Use `tests/_helpers/` for shared utilities. If pytest collects it as a test and it has zero test functions, rename it.

5. **All markers are registered** in `pyproject.toml` `[tool.pytest.ini_options].markers`. `--strict-markers` will fail if you add an unregistered marker.

6. **Use `authenticated_user_id` fixture** (from `tests/conftest.py`) instead of manually patching `get_authenticated_user_id` in 5 decorator modules.

7. **Use `full_beatmapset_dict(**overrides)`** from `tests/_helpers/data.py` for beatmapset test data.

## CI

- `.github/workflows/test.yml` defines four jobs: `lint`, `typecheck`, `unit`, `integration`.
- The `unit` job needs no services and gates PRs in seconds.
- The `integration` job uses Postgres 16 + Redis 7 service containers.