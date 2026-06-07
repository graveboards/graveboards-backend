"""
Starlette TestClient Fixture - Provides minimal Starlette TestClient for testing.

This fixture creates a minimal Starlette TestClient without loading the
full OpenAPI specification. This avoids the performance cost of loading
the large OpenAPI spec file (which takes significant time due to shallow
schema recursion).

Use this fixture when you need more control over the Starlette app configuration
than what the tests.conftest.TestClient provides.

For endpoints not explicitly configured here, tests should either:
1. Add route stubs for the specific endpoint under test
2. Use the tests.conftest.ConnexionTestClient fixture if full OpenAPI spec is needed

This module is kept for backwards compatibility but most tests should use
tests.conftest.TestClient instead.
"""

import pytest

from starlette.applications import Starlette
from starlette.testclient import TestClient as StarletteTestClient
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.oauth import OAuth


@pytest.fixture(scope="function")
def StarletteTestClient():
    """Create a TestClient for API route testing.
    
    Use this fixture when you need more control over the Starlette app
    configuration than what the conftest.TestClient provides.
    """
    async def login_endpoint(request):
        oauth = OAuth()
        authorization_url, state = oauth.create_authorization_url()
        return JSONResponse({
            "authorization_url": authorization_url,
            "state": state
        })
    
    middleware = [
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
        Middleware(GZipMiddleware),
    ]
    
    routes = [
        Route("/api/v1/login", login_endpoint, methods=["GET"]),
    ]
    
    app = Starlette(routes=routes, middleware=middleware)
    client = StarletteTestClient(app)
    
    yield client
