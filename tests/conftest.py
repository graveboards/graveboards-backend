import asyncio

import pytest

import asyncpg
import redis

from app.config import POSTGRESQL_CONFIGURATION, REDIS_CONFIGURATION


# Load benchmark hooks (optional, for performance tracking)
try:
    from .fixtures import benchmark  # noqa: F401
except ImportError:
    pass  # benchmark fixtures not available

# Load health check fixtures (optional, for fixture validation)
try:
    from .fixtures import health  # noqa: F401
except ImportError:
    pass  # health check fixtures not available


@pytest.fixture(scope="function")
def TestClient():
    """Create a minimal TestClient for fast, isolated endpoint testing.
    
    Use this fixture for Phase 3.5 (HTTP endpoint tests) that need to verify:
    - Endpoint handlers via HTTP requests
    - Middleware (CORS, GZip)
    - Parameter parsing (without full OpenAPI spec)
    
    This uses a minimal app without:
    - Lifespan setup
    - Daemon services  
    - Database connection during app creation
    
    For tests requiring database access, use the db_transaction fixture.
    
    Current routes available:
    - GET /api/v1/login - OAuth login endpoint
    """
    from starlette.testclient import TestClient
    from app.test_app import create_test_client
    
    return create_test_client()


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop


@pytest.fixture(scope="session")
async def test_db_pool():
    pool = await asyncpg.create_pool(
        host=POSTGRESQL_CONFIGURATION["host"],
        port=POSTGRESQL_CONFIGURATION["port"],
        user=POSTGRESQL_CONFIGURATION["username"],
        password=POSTGRESQL_CONFIGURATION["password"],
        database=POSTGRESQL_CONFIGURATION["database"],
    )
    yield pool
    await pool.close()


@pytest.fixture(scope="function")
async def db_transaction(test_db_pool):
    conn = await test_db_pool.acquire()
    tx = conn.transaction()
    await tx.start()
    try:
        yield conn
    finally:
        await tx.rollback()
        await test_db_pool.release(conn)


@pytest.fixture(scope="function")
async def db_session():
    """Create a SQLAlchemy async session wrapped in a transaction that auto-rolls back.
    
    Use this for most tests that don't need to control transactions manually.
    The fixture will automatically rollback after each test, ensuring isolation.
    
    For tests that need to control transaction boundaries manually (commit/rollback),
    use db_session_manual instead.
    """
    from app.database.db import PostgresqlDB
    
    db = PostgresqlDB()
    
    async with db.session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
    
    await db.close()


@pytest.fixture(scope="function")
async def db_session_manual():
    """Create a SQLAlchemy async session without automatic transaction control.
    
    Use this for tests that need full control over commit/rollback behavior.
    Tests must handle their own commit/rollback and cleanup.
    """
    from app.database.db import PostgresqlDB
    
    db = PostgresqlDB()
    
    session = db.async_session_generator()
    
    async with session() as s:
        yield s
    
    await db.close()


# Factory fixtures (for generating test data)
@pytest.fixture
def beatmap_factory():
    """Factory fixture for generating beatmap test data."""
    from tests.fixtures.factories import generate_beatmap_data
    
    class BeatmapFactory:
        def build(self, **overrides):
            data = generate_beatmap_data(count=1, **overrides)[0]
            return data
    
    return BeatmapFactory()


@pytest.fixture
def user_factory():
    """Factory fixture for generating user test data."""
    from tests.fixtures.factories import generate_user_data
    
    class UserFactory:
        def build(self, **overrides):
            data = generate_user_data(count=1, **overrides)[0]
            return data
    
    return UserFactory()


@pytest.fixture
def beatmapset_factory():
    """Factory fixture for generating beatmapset test data."""
    from tests.fixtures.factories import generate_beatmapset_data
    
    class BeatmapsetFactory:
        def build(self, **overrides):
            data = generate_beatmapset_data(count=1, **overrides)[0]
            return data
    
    return BeatmapsetFactory()


@pytest.fixture
def queue_factory():
    """Factory fixture for generating queue test data."""
    from tests.fixtures.factories import generate_beatmapset_data
    
    class QueueFactory:
        def build(self, **overrides):
            # Generate beatmapset data as base
            data = generate_beatmapset_data(count=1, **overrides)[0]
            # Add queue-specific fields
            data["name"] = overrides.get("name", f"test_queue_{data['id']}")
            data["visibility"] = overrides.get("visibility", "public")
            return data
    
    return QueueFactory()


@pytest.fixture(scope="function")
async def clean_redis():
    r = redis.Redis(
        host=REDIS_CONFIGURATION["host"],
        port=REDIS_CONFIGURATION["port"],
        db=REDIS_CONFIGURATION["db"],
        decode_responses=REDIS_CONFIGURATION["decode_responses"],
    )
    r.flushdb()
    yield r
    r.flushdb()
