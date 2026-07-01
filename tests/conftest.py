import os
from pathlib import Path

import pytest


def _clear_spec_cache() -> None:
    project_root = Path(__file__).resolve().parents[1]
    cache_files = (
        project_root / "instance" / ".spec_cache.pkl",
        project_root / "api" / "v1" / "spec" / ".spec_cache.pkl",
    )
    for cache_file in cache_files:
        if cache_file.exists():
            cache_file.unlink()


def pytest_configure(config):
    """Configure test environment before test modules are collected."""
    os.environ["DISABLE_SECURITY"] = "false"
    os.environ.setdefault("ENV", "test")
    _clear_spec_cache()


@pytest.fixture
def security_disabled():
    """Temporarily disable runtime security checks for a test."""
    from app.config import override_security_enabled

    with override_security_enabled(False):
        yield


@pytest.fixture
def security_enabled():
    """Temporarily enable runtime security checks for a test."""
    from app.config import override_security_enabled

    with override_security_enabled(True):
        yield


def TestClientWithMocksFactory(request, mock_rc=None, mock_db=None):
    """Create a TestClient with configurable mocks.
    
    Args:
        mock_rc: Optional custom Redis mock
        mock_db: Optional custom database mock
    
    Returns:
        TestClient configured with the provided mocks
    """
    from app.test_app import create_test_app
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
    from app.database.db import PostgresqlDB
    from app.database.models import Base

    db = PostgresqlDB()
    
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with db.session() as session:
        yield session
    
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await db.close()
