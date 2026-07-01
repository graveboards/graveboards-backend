"""
Integration tests for GET /api/v1/profiles endpoints.

Tests the profiles retrieval via full HTTP stack.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestProfilesGetIntegration:
    """Integration tests for GET /api/v1/profiles endpoints."""

    TEST_USER_ID = 12345678
    TEST_USER_ID_2 = 87654321

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_profiles_list(self, TestClientWithMocks, security_disabled):
        """Test admin can get profiles list."""
        from app.database.models import Profile

        mock_db = AsyncMock()
        
        profile1 = Profile()
        profile1.id = 1
        profile1.user_id = self.TEST_USER_ID
        
        profile2 = Profile()
        profile2.id = 2
        profile2.user_id = self.TEST_USER_ID_2
        
        mock_db.get_many = AsyncMock(return_value=[profile1, profile2])
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/profiles")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_profile_by_user_id(self, TestClientWithMocks, security_disabled):
        """Test admin can get profile by user id."""
        from app.database.models import Profile

        mock_db = AsyncMock()
        
        profile = Profile()
        profile.id = 1
        profile.user_id = self.TEST_USER_ID
        
        mock_db.get = AsyncMock(return_value=profile)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get(f"/api/v1/profiles/{self.TEST_USER_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == self.TEST_USER_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_profile_not_found(self, TestClientWithMocks, security_disabled):
        """Test admin gets 404 when profile doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get(f"/api/v1/profiles/{-1}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClientWithMocks, security_disabled):
        """Test security disabled bypasses authorization on profiles."""
        from app.database.models import Profile

        mock_db = AsyncMock()
        
        profile1 = Profile()
        profile1.id = 1
        profile1.user_id = self.TEST_USER_ID
        
        profile2 = Profile()
        profile2.id = 2
        profile2.user_id = self.TEST_USER_ID_2
        
        mock_db.get_many = AsyncMock(return_value=[profile1, profile2])
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/profiles")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
