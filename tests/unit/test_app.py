"""Tests for the test infrastructure itself: create_test_app, middleware, and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from connexion import AsyncApp
from starlette.testclient import TestClient


class TestCreateTestApp:
    """Test create_test_app function."""

    def test_creates_async_app(self):
        """Test create_test_app returns an AsyncApp instance."""
        from app.test_app import create_test_app
        app = create_test_app()
        assert isinstance(app, AsyncApp)

    def test_creates_with_custom_mock_rc(self):
        """Test custom mock_rc is passed through."""
        from app.test_app import create_test_app
        custom_rc = AsyncMock()
        app = create_test_app(mock_rc=custom_rc)
        assert isinstance(app, AsyncApp)

    def test_creates_with_custom_mock_db(self):
        """Test custom mock_db is passed through."""
        from app.test_app import create_test_app
        custom_db = AsyncMock()
        app = create_test_app(mock_db=custom_db)
        assert isinstance(app, AsyncApp)


class TestMockRedisMiddleware:
    """Test MockRedisMiddleware behavior."""

    def test_injects_rc_into_scope(self):
        """Test MockRedisMiddleware injects rc into ASGI scope."""
        from app.test_app import MockRedisMiddleware

        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"].get("rc") is not None)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockRedisMiddleware(inner_app)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        assert captured == [True]

    def test_accepts_custom_mock_rc(self):
        """Test custom mock_rc is used when provided."""
        from app.test_app import MockRedisMiddleware

        custom_rc = MagicMock()
        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"]["rc"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockRedisMiddleware(inner_app, mock_rc=custom_rc)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        assert captured[0] is custom_rc

    def test_default_rc_has_required_methods(self):
        """Test default mock rc has incr, expire, set, hgetall, lock_ctx."""
        from app.test_app import MockRedisMiddleware

        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"]["rc"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockRedisMiddleware(inner_app)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        rc = captured[0]
        assert hasattr(rc, "incr")
        assert hasattr(rc, "expire")
        assert hasattr(rc, "set")
        assert hasattr(rc, "hgetall")
        assert hasattr(rc, "lock_ctx")


class TestMockDatabaseMiddleware:
    """Test MockDatabaseMiddleware behavior."""

    def test_injects_db_into_scope(self):
        """Test MockDatabaseMiddleware injects db into ASGI scope."""
        from app.test_app import MockDatabaseMiddleware

        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"].get("db") is not None)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockDatabaseMiddleware(inner_app)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        assert captured == [True]

    def test_default_db_has_required_methods(self):
        """Test default mock db has get, add, update, session."""
        from app.test_app import MockDatabaseMiddleware

        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"]["db"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockDatabaseMiddleware(inner_app)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        db = captured[0]
        assert hasattr(db, "get")
        assert hasattr(db, "add")
        assert hasattr(db, "update")
        assert hasattr(db, "session")

    def test_default_user_has_correct_id(self):
        """Test default mock user has expected ID."""
        from app.test_app import MockDatabaseMiddleware

        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"]["db"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockDatabaseMiddleware(inner_app)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        db = captured[0]
        result = asyncio.run(db.get())
        assert result.id == 99999999

    def test_custom_mock_db_used(self):
        """Test custom mock_db is used when provided."""
        from app.test_app import MockDatabaseMiddleware

        custom_db = AsyncMock()
        captured = []

        async def inner_app(scope, receive, send):
            captured.append(scope["state"]["db"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = MockDatabaseMiddleware(inner_app, mock_db=custom_db)

        async def dummy_receive():
            return {"type": "http.request", "body": b""}

        async def dummy_send(message):
            pass

        import asyncio
        asyncio.run(middleware({"type": "http", "state": {}}, dummy_receive, dummy_send))

        assert captured[0] is custom_db


class TestCreateTestClient:
    """Test create_test_client helper."""

    def test_creates_test_client(self):
        """Test create_test_client returns a TestClient."""
        from app.test_app import create_test_client
        client = create_test_client()
        assert isinstance(client, TestClient)
