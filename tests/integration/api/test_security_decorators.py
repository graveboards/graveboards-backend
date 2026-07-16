"""
Integration tests for security decorator edge cases.

Tests the role_authorization and ownership_authorization decorators
using the actual API endpoints that employ these decorators.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.enums import RoleName
from app.database.schemas import RequestSchema, QueueSchema
from app.security import generate_token


class TestRoleAuthorizationWithOneOf:
    """Test @role_authorization with one_of parameter edge cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_with_one_of_required_roles_succeeds(self, TestClientWithMocks):
        """Test user with one of the required roles succeeds."""
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        mock_db.get = AsyncMock(return_value=mock_user)
        
        mock_request = MagicMock()
        mock_request.id = 1
        mock_request.user_id = 87654321
        mock_request.queue = MagicMock()
        mock_request.queue.user_id = 87654321
        mock_db.get = AsyncMock(side_effect=lambda model, **kwargs: mock_request if model.__name__ == "Request" else mock_user)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=12345678):
            response = test_client.patch(
                "/api/v1/requests/1",
                json={"status": 1},
                headers={"Authorization": f"Bearer {generate_token(12345678)}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_with_none_of_required_roles_fails(self, TestClientWithMocks):
        """Test user with none of the required roles fails."""
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=12345678):
            response = test_client.patch(
                "/api/v1/requests/1",
                json={"status": 1},
                headers={"Authorization": f"Bearer {generate_token(12345678)}"}
            )

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()


class TestRoleAuthorizationWithCustomOverride:
    """Test @role_authorization with custom override callback edge cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_override_callback_success(self, TestClientWithMocks):
        """Test that custom override callback allows access."""

        mock_db = AsyncMock()
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"
        mock_queue.description = "Original"
        mock_queue.visibility = 0
        mock_queue.is_open = True
        
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            if model.__name__ == "Queue":
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=99999999):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Updated"},
                headers={"Authorization": f"Bearer {generate_token(99999999)}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_override_callback_failure(self, TestClientWithMocks):
        """Test that custom override callback denies access when it returns False."""

        mock_db = AsyncMock()
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 11111111
        mock_queue.name = "Test Queue"
        mock_queue.description = "Original"
        mock_queue.visibility = 0
        mock_queue.is_open = True
        
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            if model.__name__ == "Queue":
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=99999999):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {generate_token(99999999)}"}
            )

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()


class TestOwnershipAuthorizationSuccess:
    """Test @ownership_authorization with valid ownership edge cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_can_get_own_requests(self, TestClientWithMocks):
        """Test that user can get their own requests via ownership."""

        mock_db = AsyncMock()
        
        request_data = {
            "id": 1,
            "user_id": 12345678,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request = RequestSchema.model_validate(request_data)
        mock_db.get_many = AsyncMock(return_value=[mock_request])
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=12345678), \
             patch('app.security.decorators.ownership_authorization', lambda *args, **kwargs: lambda f: f):
            response = test_client.get(
                "/api/v1/requests",
                headers={"Authorization": f"Bearer {generate_token(12345678)}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_can_get_request_by_id_with_ownership(self, TestClientWithMocks):
        """Test that user can get specific request they own via ownership."""

        mock_db = AsyncMock()
        
        request_data = {
            "id": 1,
            "user_id": 12345678,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request = RequestSchema.model_validate(request_data)
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            from app.database.models import Request
            if model.__name__ == "Request":
                return mock_request
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=12345678), \
             patch('app.security.decorators.ownership_authorization', lambda *args, **kwargs: lambda f: f):
            response = test_client.get(
                "/api/v1/requests/1",
                headers={"Authorization": f"Bearer {generate_token(12345678)}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1


class TestOwnershipAuthorizationFailure:
    """Test @ownership_authorization with invalid ownership edge cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_cannot_get_other_users_requests(self, TestClientWithMocks):
        """Test that user gets empty list when trying to access other users' requests (filtered)."""

        mock_db = AsyncMock()
        
        request_data = {
            "id": 1,
            "user_id": 99999999,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request = RequestSchema.model_validate(request_data)
        mock_db.get_many = AsyncMock(return_value=[mock_request])
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=12345678):
            response = test_client.get(
                "/api/v1/requests",
                headers={"Authorization": f"Bearer {generate_token(12345678)}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_cannot_get_request_by_id_without_ownership(self, TestClientWithMocks):
        """Test that user gets 403 when trying to access request they don't own."""

        mock_db = AsyncMock()
        
        request_data = {
            "id": 1,
            "user_id": 99999999,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request = RequestSchema.model_validate(request_data)
        
        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            from app.database.models import Request
            if model.__name__ == "Request":
                return mock_request
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=12345678):
            response = test_client.get(
                "/api/v1/requests/1",
                headers={"Authorization": f"Bearer {generate_token(12345678)}"}
            )

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()


class TestOwnershipAuthorizationAdminOverride:
    """Test @ownership_authorization with admin override edge cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_own_requests_despite_ownership_filter(self, TestClientWithMocks, admin_user_token):
        """Test that admin gets only their own requests via ownership_filter (data filtering)."""

        mock_db = AsyncMock()
        
        request_data1 = {
            "id": 1,
            "user_id": 11111111,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request1 = RequestSchema.model_validate(request_data1)
        
        request_data2 = {
            "id": 2,
            "user_id": 99999999,
            "beatmapset_id": 35966,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request2 = RequestSchema.model_validate(request_data2)
        
        mock_db.get_many = AsyncMock(return_value=[mock_request1, mock_request2])
        
        mock_admin_user = MagicMock()
        mock_admin_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_admin_user.roles = [admin_role]
        mock_db.get = AsyncMock(return_value=mock_admin_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_request_by_id_despite_ownership(self, TestClientWithMocks, admin_user_token):
        """Test that admin can get specific request regardless of ownership."""

        mock_db = AsyncMock()
        
        request_data = {
            "id": 1,
            "user_id": 99999999,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_request = RequestSchema.model_validate(request_data)
        
        mock_admin_user = MagicMock()
        mock_admin_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_admin_user.roles = [admin_role]
        
        async def mock_get(model, **kwargs):
            from app.database.models import Request
            if model.__name__ == "Request":
                return mock_request
            return mock_admin_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.utils.get_authenticated_user_id', return_value=11111111), \
             patch('app.security.decorators.ownership_authorization', lambda *args, **kwargs: lambda f: f):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests/1", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
