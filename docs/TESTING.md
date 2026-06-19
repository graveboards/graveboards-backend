# Testing Graveboards Backend

This project has a layered test suite with unit, integration, and e2e tests. Keep most tests fast and isolated, then add a smaller number of infrastructure-backed tests for PostgreSQL, Redis, daemon services, and osu! API behavior.

## Running Tests

### With Docker Orchestrator (Recommended)

```bash
cd graveboards-deploy
./deploy.sh test
# or on Windows: .\deploy.ps1 test
```

**Note:** The test command uses the `--profile test` Docker Compose profile to run tests in an isolated environment with separate database (graveboards_test) and Redis (DB 15) instances.

### Direct Backend

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

## Docker Testing Mode

When using the orchestrator (`./deploy.sh test`), the following configuration is used:

- **Database**: `graveboards_test`
- **Redis DB**: `15`
- **Backend Port**: `8001`
- **Frontend Port**: `3001`

This ensures tests run in isolation without interfering with dev/prod services.

## Makefile Commands

```bash
cd graveboards-backend

make test      # Run all tests
make status    # View database status
make reset     # Reset database
make seed      # Seed database
```

## Testing Best Practices

1. **Keep unit tests fast** (< 100ms each) - mock external dependencies
2. **Use fixtures for integration tests** - leverage `tests/fixtures/`
3. **Test real behavior, not implementation** - focus on inputs/outputs
4. **Clean up after tests** - ensure idempotency
5. **Use coverage reports** - aim for >80% coverage
6. **Run tests locally before committing** - prevent regressions

## CI/CD Integration

Tests run automatically on:

- Push to any branch
- Pull requests to main
- Release branches

```yaml
# Example GitHub Actions workflow
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
```

## Test Data Management

### Fixtures

Test fixtures are managed via the `manage` command:

```bash
# View fixture status
python manage.py fixtures status

# Refresh fixtures
python manage.py fixtures refresh

# Wipe all fixtures
python manage.py fixtures wipe
```

### Seeding

Seed test data:

```bash
# Seed all data
python manage.py seed all

# Seed specific category
python manage.py seed beatmaps
python manage.py seed users
```

## Debugging Tests

```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_example.py::test_example

# Run withpdb for debugging
pytest --pdb

# Run with coverage and HTML report
pytest --cov=. --cov-report=html
```
