# Test Coverage Targets

This document defines the minimum code coverage requirements for the Graveboards test suite.

## Overview

The test suite enforces minimum coverage percentages per module to ensure test quality and prevent regression.

## Coverage Requirements

### Module Coverage Targets

| Module | Minimum Coverage | Notes |
|--------|-----------------|-------|
| `app/database/` | 70% | Core DB operations |
| `app/osu_api/` | 65% | API client and parsing |
| `app/fixtures/` | 75% | Fixture management |
| `app/security/` | 80% | Security-critical code |
| `app/search/` | 60% | Search functionality |
| `app/redis/` | 65% | Redis caching |
| `app/spec/` | 50% | OpenAPI spec handling |

### Overall Project Coverage

- **Minimum**: 60%
- **Target**: 70%
- **Quality Gate**: 65% (CI will fail below this)

## Exclusions

The following are excluded from coverage:

- Test files (`tests/`)
- Migration files (`migrations/`)
- Static assets (`assets/`)
- Documentation (`docs/`)

## How to Check Coverage

### Run with coverage
```bash
pytest --cov=app --cov-report=term-missing
```

### Check specific module
```bash
pytest --cov=app/database --cov-report=term-missing
```

### Generate HTML report
```bash
pytest --cov=app --cov-report=html
```

## Enforcing Coverage

### Local Development

Before committing, ensure coverage targets are met:

```bash
pytest --cov=app --cov-fail-under=65
```

### CI/CD

The CI pipeline will fail if:

1. Overall coverage < 65%
2. Any module coverage < minimum (see table above)
3. New code has 0% coverage

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
pytest --cov=app --cov-report=term-missing --cov-report=html
open htmlcov/index.html
```

## Coverage Targets History

| Date | Overall Target | Change |
|------|---------------|--------|
| 2024-06-08 | 65% | Initial setup |

## Related Documentation

- `pytest.ini` - Coverage configuration
- `pyproject.toml` - Tool configuration
- `docs/FIXTURE_SELECTION.md` - Fixture strategies
- `tests/README.md` - Testing guidelines