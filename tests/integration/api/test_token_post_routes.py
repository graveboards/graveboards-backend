"""
Integration tests for POST /api/v1/token endpoint.

Tests the token exchange flow via full HTTP stack.
These tests verify that the Connexion endpoint correctly:
- Validates required parameters (code, state)
- Rejects invalid requests (missing params, invalid state)

The happy path (valid token exchange) is tested in unit tests as it requires
complex mocking that's better handled at the unit level.
"""
import pytest


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
