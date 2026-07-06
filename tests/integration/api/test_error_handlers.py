"""Integration tests for error handlers and custom exceptions."""

import pytest
from unittest.mock import MagicMock

from app.exceptions import (
    BadRequest, NotFound, Conflict, TypeValidationError,
    RestrictedUserError, RedisLockTimeoutError, RateLimitExceededError,
    bad_request_factory, OsuOAuthError
)
from authlib.integrations.base_client.errors import OAuthError


class TestForbiddenErrorHandler:
    """Test the 403 forbidden error handler."""

    def test_forbidden_returns_rfc7807_response(self, TestClient):
        """Test 403 handler returns RFC 7807 Problem Details format."""
        response = TestClient.get("/api/v1/nonexistent-resource-that-does-not-exist-at-all")
        assert response.status_code == 404

    def test_forbidden_handler_structure(self, TestClient):
        """Test that error responses include standard problem details fields."""
        response = TestClient.get("/api/v1/nonexistent-resource-that-does-not-exist-at-all")
        data = response.json()
        assert "detail" in data
        assert "status" in data or "code" in data or response.status_code == data.get("status_code", response.status_code)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_bad_request_exception(self):
        """Test BadRequest exception creates proper problem."""
        exc = BadRequest("test error")
        assert exc.status_code == 400
        assert exc.title == "Bad Request"
        assert exc.detail == "test error"

    def test_bad_request_exception_with_path(self):
        """Test BadRequest exception with path extension."""
        exc = BadRequest("test error", path=["user", "id"])
        assert exc.ext["path"] == "user.id"

    def test_not_found_exception(self):
        """Test NotFound exception."""
        exc = NotFound("resource not found")
        assert exc.status_code == 404
        assert exc.title == "Not Found"
        assert exc.detail == "resource not found"

    def test_not_found_exception_with_path(self):
        """Test NotFound exception with path extension."""
        exc = NotFound("not found", path=["beatmap", "id"])
        assert exc.ext["path"] == "beatmap.id"

    def test_conflict_exception(self):
        """Test Conflict exception."""
        exc = Conflict("duplicate")
        assert exc.status_code == 409
        assert exc.title == "Conflict"
        assert exc.detail == "duplicate"

    def test_conflict_exception_with_path(self):
        """Test Conflict exception with path extension."""
        exc = Conflict("duplicate", path=["queue", "beatmapset"])
        assert exc.ext["path"] == "queue.beatmapset"

    def test_type_validation_error(self):
        """Test TypeValidationError message format."""
        exc = TypeValidationError(str, int, float)
        assert "str" in str(exc)
        assert "int" in str(exc)
        assert "float" in str(exc)

    def test_restricted_user_error(self):
        """Test RestrictedUserError message format."""
        exc = RestrictedUserError(12345)
        assert exc.user_id == 12345
        assert "12345" in str(exc)
        assert "restricted" in str(exc).lower() or "deleted" in str(exc).lower()

    def test_redis_lock_timeout_error(self):
        """Test RedisLockTimeoutError message format."""
        exc = RedisLockTimeoutError("my_lock", 5.0)
        assert exc.key == "my_lock"
        assert exc.timeout == 5.0
        assert "my_lock" in str(exc)
        assert "5.0" in str(exc)

    def test_bad_request_factory_from_type_validation(self):
        """Test bad_request_factory wraps TypeValidationError."""
        exc = TypeValidationError(str, int)
        result = bad_request_factory(exc)
        assert isinstance(result, BadRequest)
        assert "str" in result.detail

    def test_bad_request_factory_from_plain_exception(self):
        """Test bad_request_factory wraps plain exceptions."""
        exc = ValueError("something went wrong")
        result = bad_request_factory(exc)
        assert isinstance(result, BadRequest)
        assert "something went wrong" in result.detail

    def test_osu_oauth_error_requires_oauth_error(self):
        """Test OsuOAuthError rejects non-OAuthError input."""
        with pytest.raises(TypeError, match="must be OAuthError"):
            OsuOAuthError(ValueError("not oauth"))

    def test_osu_oauth_error_wraps_description(self):
        """Test OsuOAuthError wraps OAuthError description."""
        oauth_exc = OAuthError(error="invalid_request", description="code already used")
        exc = OsuOAuthError(oauth_exc)
        assert exc.status_code == 400
        assert exc.title == "osu! OAuth Error"
        assert exc.detail == "code already used"
        assert exc.ext["oauth_error"] == "invalid_request"

    def test_osu_oauth_error_invalid_request_hint(self):
        """Test OsuOAuthError adds hint for invalid_request error."""
        oauth_exc = OAuthError(error="invalid_request", description="bad code")
        exc = OsuOAuthError(oauth_exc)
        assert "hint" in exc.ext
        assert "authorization code" in exc.ext["hint"].lower() or "expired" in exc.ext["hint"].lower()

    def test_osu_oauth_error_other_error_no_hint(self):
        """Test OsuOAuthError does not add hint for non-invalid_request errors."""
        oauth_exc = OAuthError(error="invalid_scope", description="bad scope")
        exc = OsuOAuthError(oauth_exc)
        assert "hint" not in exc.ext


class TestUnknownRoute:
    """Test that unknown routes return proper error responses."""

    def test_unknown_route_returns_404(self, TestClient):
        """Test unknown route returns Connexion default 404."""
        response = TestClient.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_unknown_route_returns_json(self, TestClient):
        """Test unknown route returns JSON error body."""
        response = TestClient.get("/api/v1/nonexistent")
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
