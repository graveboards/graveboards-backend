import asyncio
import os

import pytest

import asyncpg
import redis

from app.config import POSTGRESQL_CONFIGURATION, REDIS_CONFIGURATION
from app.test_app import create_test_app
from app.test_app import MockRedisMiddleware, MockDatabaseMiddleware
from app.database.db import PostgresqlDB
from app.database.models import Base


def pytest_load_initial_conftests(early_config, args, parser):
    """Configure test environment BEFORE any conftest files are loaded."""
    # Disable security for tests - MUST be set before app.config import
    os.environ["DISABLE_SECURITY"] = "true"
    os.environ["ENV"] = "test"
    # Remove .spec_cache.pkl to force fresh spec load with correct env
    cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "v1", "spec", ".spec_cache.pkl")
    if os.path.exists(cache_file):
        os.remove(cache_file)


def TestClientWithMocksFactory(request, mock_rc=None, mock_db=None):
    """Create a TestClient with configurable mocks.
    
    Args:
        mock_rc: Optional custom Redis mock
        mock_db: Optional custom database mock
    
    Returns:
        TestClient configured with the provided mocks
    """
    from starlette.testclient import TestClient
    
    test_client = TestClient(create_test_app(mock_rc=mock_rc, mock_db=mock_db))
    return test_client


@pytest.fixture
def TestClientWithMocks(request):
    """Fixture that returns a callable for creating TestClient with mocks.
    
    This fixture provides a factory function that can be used to create
    TestClient instances with custom mocks.
    
    Returns:
        A callable that accepts mock_rc and mock_db parameters
    """
    return lambda **kwargs: TestClientWithMocksFactory(request, **kwargs)


@pytest.fixture
def TestClient():
    """Create a basic TestClient without mocks for HTTP endpoint testing.
    
    Returns:
        TestClient instance with real app configuration
    """
    from starlette.testclient import TestClient
    from app.test_app import create_test_app
    
    test_client = TestClient(create_test_app())
    return test_client


@pytest.fixture
def admin_user_token():
    """Generate a JWT token for admin user.
    
    Returns:
        Signed JWT string for user ID 11111111 (admin)
    """
    from app.security import generate_token
    return generate_token(11111111)


@pytest.fixture(scope="function")
async def db_session():
    """Create a database session for CRUD operations.
    
    Uses PostgresqlDB with automatic transaction rollback between tests
    to ensure test isolation.
    
    Yields:
        AsyncSession: Database session for the test
    """
    db = PostgresqlDB()
    
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with db.session() as session:
        yield session
    
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await db.close()
