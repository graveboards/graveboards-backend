# Test Coverage Targets

This document defines the minimum code coverage requirements for the Graveboards test suite.

## Overview

The test suite enforces minimum coverage percentages to ensure test quality and prevent regression. Coverage is configured in `pyproject.toml` via `addopts`.

## Coverage Requirements

### Overall Project Coverage

- **Minimum (enforced)**: 70%
- Configured in `pytest.ini` and `pyproject.toml` as `--cov-fail-under=70`
- CI fails if overall coverage drops below this threshold

### Module Coverage Goals

These are aspirational targets, not hard enforcement. Focus on writing meaningful tests rather than chasing percentages:

| Module | Target | Notes |
|--------|--------|-------|
| `app/database/` | 70% | Core DB operations |
| `app/osu_api/` | 65% | API client and parsing |
| `app/fixtures/` | 75% | Fixture management |
| `app/security/` | 80% | Security-critical code |
| `app/search/` | 60% | Search functionality |
| `app/redis/` | 65% | Redis caching |
| `app/spec/` | 50% | OpenAPI spec handling |

## Exclusions

The following are excluded from coverage:

- Test files (`tests/`)
- Migration files (`alembic/versions/`)
- Static assets (`assets/`)
- Documentation (`docs/`)

## How to Check Coverage

### Run with coverage
```bash
pytest --cov=app --cov=api --cov-report=term-missing
```

### Check specific module
```bash
pytest --cov=app/database --cov-report=term-missing
```

### Generate HTML report
```bash
pytest --cov=app --cov=api --cov-report=html
```

### Enforce minimum locally
```bash
pytest --cov=app --cov=api --cov-fail-under=70
```

## Enforcing Coverage

### Local Development

Before committing, ensure coverage targets are met:

```bash
pytest --cov=app --cov=api --cov-fail-under=70
```

### CI/CD

The CI pipeline will fail if overall coverage is below 70%.

## Coverage Best Practices

### What to Test

- ✅ All public functions/methods
- ✅ Error handling paths
- ✅ Edge cases and boundary conditions
- ✅ State transitions
- ✅ External API calls (with mocking)

### What Not to Test

- ❌ Private methods (tested indirectly through public API)
- ❌ Simple setters/getters
- ❌ Type annotations
- ❌ Logging statements

### Increasing Coverage

1. Add tests for uncovered branches
2. Test error paths with proper fixtures
3. Use parametrized tests for multiple inputs
4. Mock external dependencies properly
5. Test integration points

## Coverage Dashboard

View coverage trends over time:

```bash
pytest --cov=app --cov=api --cov-report=term-missing --cov-report=html
open htmlcov/index.html
```

## Related Documentation

- `pyproject.toml` - Coverage configuration (`--cov-fail-under=70`)
- `docs/FIXTURE_SELECTION.md` - Fixture strategies
- `docs/TESTING.md` - Testing guidelines
