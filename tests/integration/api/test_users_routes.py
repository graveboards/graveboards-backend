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
    async def test_admin_can_get_users_list(self, TestClientWithMocks, security_disabled):
        """Test admin can get users list."""
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
    async def test_admin_can_get_user_by_id(self, TestClientWithMocks, security_disabled):
        """Test admin can get user by id."""
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
    async def test_admin_user_not_found(self, TestClientWithMocks, security_disabled):
        """Test admin gets 404 when user doesn't exist."""
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
    async def test_bypass_security_with_flag(self, TestClientWithMocks, security_disabled):
        """Test security disabled bypasses authorization."""
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


class TestUsersPostIntegration:
    """Integration tests for POST /api/v1/users endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_user_success(self, TestClientWithMocks, admin_user_token):
        """Test successful user creation."""
        from app.database.models import User
        from app.database.enums import RoleName

        mock_db = AsyncMock()

        mock_admin_user = MagicMock()
        mock_admin_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN
        mock_admin_user.roles = [admin_role]

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return mock_admin_user
            if model == User:
                return None
            return mock_admin_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                "/api/v1/users",
                json={"id": 99999999, "roles": []},
                headers=headers
            )

        assert response.status_code == 201
        data = response.json()
        assert "added successfully" in data["message"].lower()
        mock_db.add.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_user_conflict(self, TestClientWithMocks, admin_user_token):
        """Test 409 when user already exists."""
        from app.database.models import User
        from app.database.enums import RoleName

        mock_db = AsyncMock()

        mock_admin_user = MagicMock()
        mock_admin_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN
        mock_admin_user.roles = [admin_role]

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return mock_admin_user
            if model == User:
                return MagicMock(id=99999999)
            return mock_admin_user

        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                "/api/v1/users",
                json={"id": 99999999, "roles": []},
                headers=headers
            )

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
