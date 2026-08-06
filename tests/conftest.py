"""
Test configuration and shared fixtures for the Graveboards backend test suite.

Fixture hierarchy:
- db_session: Creates tables, rolls back after each test (test isolation)
- db_transaction: Creates tables, commits after each test (visible to search queries)
- TestClient: Full Connexion app with mock middleware (no real Redis/DB)
- test_client_with_mocks: TestClient with injectable mock_rc and mock_db
- admin_user_token: JWT for admin user ID 11111111
- security_disabled: Context manager to bypass security decorators
- security_enabled: Context manager to enforce security decorators
- authenticated_user_id: Patches get_authenticated_user_id in all decorator modules
"""

import os
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

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


def pytest_configure(config: Any) -> None:
    """Configure test environment before test modules are collected."""
    os.environ["DISABLE_SECURITY"] = "false"
    os.environ.setdefault("ENV", "test")
    _clear_spec_cache()


@pytest.fixture
def security_disabled() -> Any:
    """Temporarily disable runtime security checks for a test."""
    from app.config import override_security_enabled

    with override_security_enabled(False):
        yield


@pytest.fixture
def security_enabled() -> Any:
    """Temporarily enable runtime security checks for a test."""
    from app.config import override_security_enabled

    with override_security_enabled(True):
        yield


@pytest.fixture
def authenticated_user_id() -> Callable[[int], Any]:
    """Fixture that returns a context-manager factory to patch
    ``get_authenticated_user_id`` in every decorator module.

    Each decorator module (``role_authorization``, ``auth_context``,
    ``ownership_authorization``, ``ownership_filter``) imports
    ``get_authenticated_user_id`` via ``from .utils import get_authenticated_user_id``,
    which creates a local reference.  Patching only the source module
    (``app.security.decorators.utils``) is therefore not enough - we must patch
    every consumer module so the desired user ID flows through every decorator.

    Usage::

        def test_something(self, authenticated_user_id) -> None:
            with authenticated_user_id(99999999):
                ...
    """

    def _patch(user_id: int) -> Any:
        stack = ExitStack()
        for module in (
            "app.security.decorators.role_authorization",
            "app.security.decorators.auth_context",
            "app.security.decorators.ownership_authorization",
            "app.security.decorators.ownership_filter",
            "app.security.decorators.utils",
        ):
            stack.enter_context(patch(f"{module}.get_authenticated_user_id", return_value=user_id))
        return stack

    return _patch


def _patch_all_auth_modules(user_id: int) -> ExitStack:
    """Return a context manager that patches ``get_authenticated_user_id`` in every
    decorator module that imports it.

    Each decorator module (``role_authorization``, ``auth_context``,
    ``ownership_authorization``, ``ownership_filter``) imports
    ``get_authenticated_user_id`` via ``from .utils import get_authenticated_user_id``,
    which creates a local reference.  Patching only the source module
    (``app.security.decorators.utils``) is therefore not enough - we must patch
    every consumer module so the desired user ID flows through every decorator.
    """
    stack = ExitStack()
    for module in (
        "app.security.decorators.role_authorization",
        "app.security.decorators.auth_context",
        "app.security.decorators.ownership_authorization",
        "app.security.decorators.ownership_filter",
        "app.security.decorators.utils",
    ):
        stack.enter_context(patch(f"{module}.get_authenticated_user_id", return_value=user_id))
    return stack


def test_client_with_mocks_factory(request: Any, mock_rc: Any = None, mock_db: Any = None) -> Any:
    """Create a TestClient with configurable mocks.

    Args:
        mock_rc: Optional custom Redis mock
        mock_db: Optional custom database mock

    Returns:
        TestClient configured with the provided mocks
    """
    from starlette.testclient import TestClient

    from app.test_app import create_test_app

    return TestClient(create_test_app(mock_rc=mock_rc, mock_db=mock_db))


@pytest.fixture
def test_client_with_mocks(request: Any) -> Any:
    """Fixture that returns a callable for creating TestClient with mocks.

    This fixture provides a factory function that can be used to create
    TestClient instances with custom mocks.

    Returns:
        A callable that accepts mock_rc and mock_db parameters
    """
    return lambda **kwargs: test_client_with_mocks_factory(request, **kwargs)


@pytest.fixture
def test_client() -> Any:
    """Create a basic TestClient without mocks for HTTP endpoint testing.

    Returns:
        TestClient instance with real app configuration
    """
    from starlette.testclient import TestClient

    from app.test_app import create_test_app

    return TestClient(create_test_app())


@pytest.fixture
def admin_user_token() -> str:
    """Generate a JWT token for admin user.

    Returns:
        Signed JWT string for user ID 11111111 (admin)
    """
    from app.security import generate_token

    return str(generate_token(11111111))


@pytest.fixture
async def db_session() -> Any:
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
        await conn.run_sync(lambda c: Base.metadata.create_all(c))

    async with db.session() as session:
        yield session

    async with db.engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.drop_all(c))

    await db.close()


@pytest.fixture
async def db_transaction() -> Any:
    """Create a database session that commits changes.

    Unlike db_session, this fixture commits changes so seeded data
    is visible to search queries within the test.

    Yields:
        AsyncSession: Database session for the test
    """
    from app.database.db import PostgresqlDB
    from app.database.models import Base

    db = PostgresqlDB()

    async with db.engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c))

    async with db.session() as session:
        yield session
        await session.commit()

    async with db.engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.drop_all(c))

    await db.close()
