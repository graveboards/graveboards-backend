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
    from app.test_app import create_test_client

    return create_test_client()


@pytest.fixture(scope="function")
def TestClientWithMocks():
    """Create a TestClient with custom mock objects injected into middleware.
    
    Use this for tests that need isolated mock objects to avoid middleware pollution.
    Each test gets its own middleware instances with its own mocks.
    
    Args:
        mock_rc: Optional mock Redis client
        mock_db: Optional mock database client
        
    Returns:
        A TestClient with middleware instances that use the provided mocks
    """
    from app.test_app import create_test_app
    from starlette.testclient import TestClient

    def _create_client(mock_rc=None, mock_db=None):
        app = create_test_app(mock_rc=mock_rc, mock_db=mock_db)
        return TestClient(app)

    return _create_client


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop


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


@pytest.fixture
def admin_user_token():
    """Generate JWT for admin user (PRIMARY_ADMIN_USER_ID)."""
    from app.security import create_token_payload, encode_token
    from app.config import PRIMARY_ADMIN_USER_ID

    payload = create_token_payload(PRIMARY_ADMIN_USER_ID)
    return encode_token(payload)


@pytest.fixture
def mock_beatmap_manager():
    """Factory fixture for creating BeatmapManager mocks."""
    from unittest.mock import MagicMock, AsyncMock

    def _create_manager(result):
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value=result)
        return mock_bm

    return _create_manager


@pytest.fixture
def mock_rc():
    """Fixture for creating mock Redis client."""
    from unittest.mock import AsyncMock

    mock_rc = AsyncMock()
    mock_rc.hgetall = AsyncMock(return_value=None)
    mock_rc.getdel = AsyncMock(return_value=None)
    mock_rc.hset = AsyncMock(return_value=True)
    mock_rc.expire = AsyncMock(return_value=True)
    return mock_rc


@pytest.fixture
def mock_osu_client(mock_rc):
    """Fixture for creating mock OsuAPIClient."""
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.rc = mock_rc
    return mock_client


@pytest.fixture
def mock_db_session():
    """Fixture for creating mock database session."""
    from unittest.mock import MagicMock, AsyncMock

    mock = MagicMock()
    mock.get = AsyncMock()
    mock.add = AsyncMock()
    mock.update = AsyncMock()
    return mock


@pytest.fixture
def mock_db_with_side_effect():
    """Fixture for creating mock database with custom get side effects."""
    from unittest.mock import AsyncMock

    def _create_db(*side_effects):
        mock = AsyncMock()
        mock.get = AsyncMock(side_effect=list(side_effects))
        mock.add = AsyncMock()
        return mock

    return _create_db
