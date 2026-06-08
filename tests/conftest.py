import asyncio

import pytest

import asyncpg
import redis

from app.config import POSTGRESQL_CONFIGURATION, REDIS_CONFIGURATION


@pytest.fixture(scope="function")
def MinimalTestClient():
    """Create a TestClient using the full Connexion app with lifespan.
    
    Use this fixture for Phase 6 (full E2E tests) that need to verify:
    - Full OpenAPI parameter parsing
    - Endpoint handlers via real API routes
    - Full app lifecycle (lifespan, middleware, auth, DB)
    
    This loads the full OpenAPI spec and all registered routes.
    Tests run slower (~300-500ms) due to full app startup.
    
    For fast Phase 3.5 endpoint tests, use TestClient fixture instead.
    """
    from starlette.testclient import TestClient
    from app.connexion_app import create_connexion_app
    
    app = create_connexion_app()
    with TestClient(app.app) as client:
        yield client


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
