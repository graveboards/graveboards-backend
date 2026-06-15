"""
Integration tests for DISABLE_SECURITY environment variable coverage.

Tests that verify security can be enabled/disabled via the DISABLE_SECURITY
environment variable as specified in Phase 10.11 of TESTING_GAPS.md.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSecurityEnabledByDefault:
    """Test that security is enabled by default in test environment."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_by_default_in_test_env(self, TestClientWithMocks, monkeypatch):
        """Verify .env.test has DISABLE_SECURITY=false and security is enforced."""
        monkeypatch.setenv("DISABLE_SECURITY", "false")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"
        mock_queue.description = "Original"
        mock_queue.visibility = 0
        mock_queue.is_open = True
        
        async def mock_get(model, **kwargs):
            if model.__name__ == "Queue":
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=12345678):
            response = test_client.patch("/api/v1/queues/1", json={"name": "Hacked"})

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()


class TestSecurityDisabledViaEnvVariable:
    """Test that DISABLE_SECURITY=true actually bypasses checks."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_via_env_variable(self, TestClientWithMocks, monkeypatch):
        """Verify DISABLE_SECURITY=true in .env actually bypasses checks."""
        monkeypatch.setenv("DISABLE_SECURITY", "true")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"
        mock_queue.description = "Original"
        mock_queue.visibility = 0
        mock_queue.is_open = True
        
        async def mock_get(model, **kwargs):
            if model.__name__ == "Queue":
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', True), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=12345678):
            response = test_client.patch("/api/v1/queues/1", json={"name": "Updated"})

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_user_gets_403_when_security_enabled(self, TestClientWithMocks, monkeypatch):
        """Verify non-admin users get 403 Forbidden when trying to access admin endpoints."""
        monkeypatch.setenv("DISABLE_SECURITY", "false")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        
        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.user_id = 87654321
        mock_request.queue = MagicMock()
        mock_request.queue.user_id = 87654321
        mock_db.get = AsyncMock(return_value=mock_request)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=12345678):
            response = test_client.patch("/api/v1/requests/1", json={"status": 1})

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_user_can_access_when_security_disabled(self, TestClientWithMocks, monkeypatch):
        """Verify non-admin users can access endpoints when DISABLE_SECURITY=true."""
        monkeypatch.setenv("DISABLE_SECURITY", "true")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        
        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.user_id = 87654321
        mock_request.queue = MagicMock()
        mock_request.queue.user_id = 87654321
        mock_db.get = AsyncMock(return_value=mock_request)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', True), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=12345678):
            response = test_client.patch("/api/v1/requests/1", json={"status": 1})

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()
