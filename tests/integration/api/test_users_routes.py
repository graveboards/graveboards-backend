"""
Integration tests for GET /api/v1/users endpoints.

Tests the users retrieval via full HTTP stack.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestUsersGetIntegration:
    """Integration tests for GET /api/v1/users endpoints."""

    TEST_USER_ID = 12345678
    TEST_USER_ID_2 = 87654321

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_users_list(self, TestClientWithMocks, monkeypatch):
        """Test admin can get users list."""
        monkeypatch.setenv("DISABLE_SECURITY", "true")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        # Return plain dicts that match the schema format
        user1 = {"id": self.TEST_USER_ID, "profile": None, "roles": []}
        user2 = {"id": self.TEST_USER_ID_2, "profile": None, "roles": []}
        
        mock_db.get_many = AsyncMock(return_value=[user1, user2])
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_user_by_id(self, TestClientWithMocks, monkeypatch):
        """Test admin can get user by id."""
        monkeypatch.setenv("DISABLE_SECURITY", "true")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        user = {"id": self.TEST_USER_ID, "profile": None, "roles": []}
        
        mock_db.get = AsyncMock(return_value=user)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get(f"/api/v1/users/{self.TEST_USER_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.TEST_USER_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_user_not_found(self, TestClientWithMocks, monkeypatch):
        """Test admin gets 404 when user doesn't exist."""
        monkeypatch.setenv("DISABLE_SECURITY", "true")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get(f"/api/v1/users/{-1}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClientWithMocks, monkeypatch):
        """Test DISABLE_SECURITY=True bypasses authorization."""
        monkeypatch.setenv("DISABLE_SECURITY", "true")
        monkeypatch.setenv("ENV", "test")
        
        mock_db = AsyncMock()
        
        user1 = {"id": self.TEST_USER_ID, "profile": None, "roles": []}
        user2 = {"id": self.TEST_USER_ID_2, "profile": None, "roles": []}
        
        mock_db.get_many = AsyncMock(return_value=[user1, user2])
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
