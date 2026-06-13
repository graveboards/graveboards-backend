"""
Integration tests for POST /api/v1/token endpoint.

Tests the token exchange flow via full HTTP stack.
These tests verify that the Connexion endpoint correctly:
- Validates required parameters (code, state)
- Rejects invalid requests (missing params, invalid state)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone


class TestTokenPostIntegration:
    """Integration tests for POST /api/v1/token endpoint."""

    TEST_STATE = "test_csrf_state_12345"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_exchange_missing_code(self, TestClient):
        """Test POST /api/v1/token with missing code returns 400."""
        body = f"state={self.TEST_STATE}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = TestClient.post("/api/v1/token", data=body, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "code" in data["detail"].lower() or "Missing" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_exchange_missing_state(self, TestClient):
        """Test POST /api/v1/token with missing state returns 400."""
        body = f"code=test_code"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = TestClient.post("/api/v1/token", data=body, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "state" in data["detail"].lower() or "Missing" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_exchange_success(self, TestClient):
        """Test successful token exchange via HTTP stack with mocked dependencies."""
        state = "test_csrf_state_12345"
        code = "test_authorization_code"

        body = f"code={code}&state={state}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async def async_mock_fetch_token(*args, **kwargs):
            return {
                "access_token": "test_access_token_xyz",
                "refresh_token": "test_refresh_token_abc",
                "expires_at": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            }

        async def async_mock_get_own_data(*args, **kwargs):
            return {
                "id": 12345678,
                "username": "test_user",
                "avatar_url": "https://example.com/avatar.png",
            }

        mock_oauth = AsyncMock()
        mock_oauth.fetch_token = AsyncMock(side_effect=async_mock_fetch_token)

        mock_osu_client = AsyncMock()
        mock_osu_client.get_own_data = AsyncMock(side_effect=async_mock_get_own_data)

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_db.get = AsyncMock(return_value=mock_user)
        mock_db.add = AsyncMock()
        mock_db.update = AsyncMock()

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            with patch('app.oauth.OAuth', return_value=mock_oauth), \
                 patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client), \
                 patch('api.v1.token.OAuth', return_value=mock_oauth), \
                 patch('api.v1.token.OsuAPIClient', return_value=mock_osu_client):
                response = TestClient.post("/api/v1/token", data=body, headers=headers)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0
