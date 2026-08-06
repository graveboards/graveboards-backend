"""Test application factory with isolated startup for testing."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

from connexion import AsyncApp
from connexion.exceptions import Forbidden
from connexion.middleware import MiddlewarePosition
from connexion.resolver import RestyResolver
from connexion.security import ApiKeySecurityHandler, BearerSecurityHandler
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.testclient import TestClient

from app.config import (
    CONFIG,
    DEBUG_API_KEY,
    DEFAULT_MODULE_NAME,
    JWT_SECRET_KEY,
    SPEC_DIR,
)
from app.error_handlers import forbidden
from app.patches import OpenAPIURIParserPatched, ParameterValidatorPatched
from app.redis_client import RedisClient
from app.spec import load_spec

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.applications import Starlette
    from starlette.types import Receive, Send


def _patch_connexion_request_injection() -> None:
    """Patch connexion's parameter decorator to pass `request` to handlers.

    Connexion 3.x's AsyncParameterDecorator calls ``function(**kwargs``) which
    only contains path/query/body/file params — the ``request`` object itself
    is NOT included.  All our handlers expect ``request: Request`` as the first
    positional argument, so we must inject it into ``kwargs``.
    """
    import connexion.decorators.parameter as param_module

    original_prep_kwargs = param_module.prep_kwargs

    def patched_prep_kwargs(
        request: Any,
        *,
        request_body: Any,
        files: dict[str, Any],
        arguments: list[str],
        has_kwargs: bool,
        sanitize: Callable,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = original_prep_kwargs(
            request,
            request_body=request_body,
            files=files,
            arguments=arguments,
            has_kwargs=has_kwargs,
            sanitize=sanitize,
        )
        # Inject the request object if the handler expects it
        if "request" in arguments or has_kwargs:
            kwargs["request"] = request
        return kwargs

    param_module.prep_kwargs = patched_prep_kwargs


class MockRedisMiddleware:
    """Minimal Redis middleware for testing.

    Provides a mock Redis client with async methods for testing endpoints
    that require Redis in request.state without needing the full app setup.

    Accepts optional mock_rc parameter for custom Redis mock objects.
    """

    def __init__(self, app: Starlette, mock_rc: Any = None) -> None:
        self.app = app
        self.mock_rc = mock_rc

    async def __call__(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        """Process an ASGI request with mock Redis.

        Args:
            scope:
                The ASGI scope.
            receive:
                The ASGI receive callable.
            send:
                The ASGI send callable.
        """
        from unittest.mock import MagicMock

        if self.mock_rc is not None:
            rc = self.mock_rc
        else:
            rc = AsyncMock(spec=RedisClient)
            rc.ttl = AsyncMock(return_value=0)
            rc.incr = AsyncMock(return_value=1)
            rc.expire = AsyncMock(return_value=True)
            rc.set = AsyncMock(return_value=True)
            rc.hgetall = AsyncMock()
            rc.hgetall.return_value = None
            rc.hset = AsyncMock(return_value=True)
            rc.getdel = AsyncMock(return_value="valid")
            rc.delete = AsyncMock(return_value=0)

            class MockLockCtx:
                async def __aenter__(self) -> None:
                    return None

                async def __aexit__(self, *args: Any) -> bool | None:
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

    def __init__(self, app: Starlette, mock_db: Any = None) -> None:
        self.app = app
        self.mock_db = mock_db

    async def __call__(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        """Process an ASGI request with mock database.

        Args:
            scope:
                The ASGI scope.
            receive:
                The ASGI receive callable.
            send:
                The ASGI send callable.
        """
        from unittest.mock import MagicMock

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
                def __init__(self, autoflush: bool = True) -> None:
                    self.autoflush = autoflush

                async def __aenter__(self) -> MagicMock:
                    return MagicMock()

                async def __aexit__(self, *args: Any) -> bool | None:
                    pass

            db.session = MockSession

        scope["state"]["db"] = db
        await self.app(scope, receive, send)


def get_debug_api_key() -> str:
    """Get or generate a debug API key for testing."""
    if DEBUG_API_KEY:
        return DEBUG_API_KEY

    bootstrap = CONFIG.bootstrap
    primary_user_id = bootstrap.initial_users[0].user_id if bootstrap.initial_users else 0
    seed = f"{JWT_SECRET_KEY}:{primary_user_id}:debug-api-key"
    return str(__import__("hashlib").sha256(seed.encode()).hexdigest()[:32])


class TestBearerSecurityHandler(BearerSecurityHandler):
    """No-op Bearer security handler for tests.

    Accepts any Bearer token without validation.
    """

    def _get_verify_func(self, _token_info_func: Any) -> Callable[[Any], dict[str, str | bool]]:
        def wrapper(_request: Any) -> dict[str, str | bool]:
            return {"sub": "0", "test": True}

        return wrapper


class TestApiKeySecurityHandler(ApiKeySecurityHandler):
    """No-op API key security handler for tests.

    Accepts any API key without validation.
    """

    def _get_verify_func(
        self, _api_key_info_func: Any, _loc: str, _name: str, _required_scopes: list[str]
    ) -> Callable[[Any], bool]:
        def wrapper(_request: Any) -> bool:
            return True

        return wrapper


def create_test_app(mock_rc: Any = None, mock_db: Any = None) -> AsyncApp:
    """Create a minimal Connexion app for testing.

    This creates an app without:
    - Full lifespan (no daemon startup, no production setup)
    - Real osu! API calls during startup

    Use with TestClient for fast, isolated endpoint tests.

    Args:
        mock_rc: Optional custom Redis mock to inject into MockRedisMiddleware
        mock_db: Optional custom database mock to inject into MockDatabaseMiddleware
    """
    _patch_connexion_request_injection()

    connexion_app = AsyncApp(
        __name__,
        specification_dir=SPEC_DIR,
        uri_parser_class=OpenAPIURIParserPatched,
        validator_map={"parameter": ParameterValidatorPatched},
    )

    connexion_app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    connexion_app.add_middleware(GZipMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION)
    connexion_app.add_middleware(
        MockRedisMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION, mock_rc=mock_rc
    )
    connexion_app.add_middleware(
        MockDatabaseMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION, mock_db=mock_db
    )

    class NoopRequestBodyValidator:
        """No-op validator that accepts all request bodies."""

        async def validate(self, _request: Any) -> None:
            return None

    validator_map = {"parameter": ParameterValidatorPatched}
    if not os.getenv("GRAVEBOARDS_USE_PRODUCTION_VALIDATOR"):
        validator_map["body"] = {"*/*": NoopRequestBodyValidator()}

    connexion_app.add_api(
        load_spec(),
        resolver=RestyResolver(DEFAULT_MODULE_NAME),
        validator_map=validator_map,
        auth_all_paths=True,
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
