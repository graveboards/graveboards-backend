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
    DISABLE_SECURITY,
)
from app.lifespan import lifespan as production_lifespan
from app.patches import OpenAPIURIParserPatched, ParameterValidatorPatched
from app.spec import load_spec
from app.error_handlers import forbidden


def get_debug_api_key() -> str:
    """Get or generate a debug API key for testing."""
    if DEBUG_API_KEY:
        return DEBUG_API_KEY

    seed = f"{JWT_SECRET_KEY}:{PRIMARY_ADMIN_USER_ID}:debug-api-key"
    return __import__('hashlib').sha256(seed.encode()).hexdigest()[:32]


def create_test_app() -> AsyncApp:
    """Create a minimal Connexion app for testing.
    
    This creates an app without:
    - Full lifespan (no daemon startup, no production setup)
    - Real osu! API calls during startup
    
    Use with TestClient for fast, isolated endpoint tests.
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

    connexion_app.add_api(
        load_spec(),
        resolver=RestyResolver(DEFAULT_MODULE_NAME)
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
