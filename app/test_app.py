"""
Test App Module - Provides isolated app startup for testing.

This module provides app creation functions that:
1. Skip expensive non-test initialization (daemon services, API calls)
2. Use test-specific configuration (in-memory DB, test Redis, etc.)
3. Provide clean isolation between tests
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Never
from unittest.mock import AsyncMock

from connexion import AsyncApp
from connexion.exceptions import Forbidden
from connexion.middleware import MiddlewarePosition
from connexion.resolver import RestyResolver
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.testclient import TestClient

from app.config import (
    SPEC_DIR,
    DEFAULT_MODULE_NAME,
    DEBUG,
    DEBUG_API_KEY,
    JWT_SECRET_KEY,
    PRIMARY_ADMIN_USER_ID,
)
from app.lifespan import lifespan as production_lifespan
from app.patches import OpenAPIURIParserPatched, ParameterValidatorPatched
from app.spec import load_spec
from app.error_handlers import forbidden
from app.redis import RedisClient


class MockRedisMiddleware:
    """Minimal Redis middleware for testing.
    
    Provides a mock Redis client with async methods for testing endpoints
    that require Redis in request.state without needing the full app setup.
    
    Accepts optional mock_rc parameter for custom Redis mock objects.
    """

    def __init__(self, app, mock_rc=None):
        self.app = app
        self.mock_rc = mock_rc

    async def __call__(self, scope, receive, send):
        from unittest.mock import AsyncMock, MagicMock
        
        if self.mock_rc is not None:
            rc = self.mock_rc
        else:
            rc = AsyncMock(spec=RedisClient)
            rc.incr = AsyncMock(return_value=1)
            rc.expire = AsyncMock(return_value=True)
            rc.set = AsyncMock(return_value=True)
            rc.hgetall = AsyncMock()
            rc.hgetall.return_value = None
            rc.hset = AsyncMock(return_value=True)
            rc.getdel = AsyncMock(return_value="valid")
            
            class MockLockCtx:
                async def __aenter__(self):
                    return None
                async def __aexit__(self, *args):
                    pass
            
            rc.lock_ctx = MagicMock(return_value=MockLockCtx())
        
        scope["state"]["rc"] = rc
        await self.app(scope, receive, send)


class MockDatabaseMiddleware:
    """Minimal database middleware for testing.
    
    Provides a mock database connection for testing endpoints
    that require db in request.state without needing the full app setup.
    
    Accepts optional mock_db parameter for custom database mock objects.
    """

    def __init__(self, app, mock_db=None):
        self.app = app
        self.mock_db = mock_db

    async def __call__(self, scope, receive, send):
        from unittest.mock import AsyncMock, MagicMock
        
        if self.mock_db is not None:
            db = self.mock_db
        else:
            db = AsyncMock()
            
            mock_user = MagicMock()
            mock_user.id = scope["state"].get("test_user_id", 99999999)
            mock_user.roles = scope["state"].get("test_user_roles", [])
            
            db.get = AsyncMock(return_value=mock_user)
            db.add = AsyncMock()
            db.update = AsyncMock()
            
            class MockSession:
                def __init__(self, autoflush=True):
                    self.autoflush = autoflush
                
                async def __aenter__(self):
                    return MagicMock()
                async def __aexit__(self, *args):
                    pass
            
            db.session = MockSession
        
        scope["state"]["db"] = db
        await self.app(scope, receive, send)


def get_debug_api_key() -> str:
    """Get or generate a debug API key for testing."""
    if DEBUG_API_KEY:
        return DEBUG_API_KEY

    seed = f"{JWT_SECRET_KEY}:{PRIMARY_ADMIN_USER_ID}:debug-api-key"
    return __import__('hashlib').sha256(seed.encode()).hexdigest()[:32]


def create_test_app(mock_rc=None, mock_db=None) -> AsyncApp:
    """Create a minimal Connexion app for testing.
    
    This creates an app without:
    - Full lifespan (no daemon startup, no production setup)
    - Real osu! API calls during startup
    
    Use with TestClient for fast, isolated endpoint tests.
    
    Args:
        mock_rc: Optional custom Redis mock to inject into MockRedisMiddleware
        mock_db: Optional custom database mock to inject into MockDatabaseMiddleware
    """
    connexion_app = AsyncApp(
        __name__,
        specification_dir=SPEC_DIR,
        uri_parser_class=OpenAPIURIParserPatched,
        validator_map={
            "parameter": ParameterValidatorPatched
        }
    )

    connexion_app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    connexion_app.add_middleware(
        GZipMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION
    )
    connexion_app.add_middleware(
        MockRedisMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        mock_rc=mock_rc
    )
    connexion_app.add_middleware(
        MockDatabaseMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        mock_db=mock_db
    )

    from connexion.lifecycle import ConnexionResponse
    
    class NoopRequestBodyValidator:
        """No-op validator that accepts all request bodies."""
        async def validate(self, request):
            return None

    connexion_app.add_api(
        load_spec(),
        resolver=RestyResolver(DEFAULT_MODULE_NAME),
        validator_map={
            "parameter": ParameterValidatorPatched,
            "body": {"*/*": NoopRequestBodyValidator()},
        }
    )

    connexion_app.add_error_handler(Forbidden, forbidden)

    return connexion_app


def create_test_client() -> TestClient:
    """Create a TestClient for fast, isolated endpoint testing.
    
    This client uses a minimal app without:
    - Lifespan setup
    - Daemon services
    - Database connection during app creation
    
    For tests requiring database access, use the db_transaction fixture.
    """
    app = create_test_app()
    return TestClient(app)
