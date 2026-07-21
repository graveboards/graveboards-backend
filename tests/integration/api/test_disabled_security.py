"""
Integration tests for security configuration.

Tests verify that security decorators work correctly with the
get_security_enabled() configuration mechanism.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSecurityConfiguration:
    """Test security decorator behavior with configuration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_by_default(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Verify security is enabled by default in test environment."""
        from app.database.models import Queue

        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"
        
        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_can_be_disabled_per_test(self, TestClientWithMocks, security_disabled, authenticated_user_id):
        """Verify security can be disabled for specific tests."""
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"
        mock_db.get = AsyncMock(return_value=mock_queue)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch("/api/v1/queues/1", json={"name": "Updated"})

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_enforces_auth(self, TestClientWithMocks, admin_user_token, security_enabled, authenticated_user_id):
        """Verify security enforcement when explicitly enabled."""
        from app.database.models import Queue

        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        
        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

        assert response.status_code == 403
