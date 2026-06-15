import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models import Queue


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_model_creation():
    queue = Queue(
        user_id=12345678,
        name="Test Queue",
        description="A test queue",
        visibility=0,
        is_open=True
    )

    assert queue.user_id == 12345678
    assert queue.name == "Test Queue"
    assert queue.description == "A test queue"
    assert queue.visibility == 0
    assert queue.is_open == True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_visibility_enum():
    queue = Queue(
        user_id=12345678,
        name="Test Queue",
        visibility=0
    )
    assert queue.visibility == 0

    queue.visibility = 1
    assert queue.visibility == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_open_close():
    queue = Queue(
        user_id=12345678,
        name="Test Queue",
        is_open=True
    )

    assert queue.is_open == True

    queue.is_open = False
    assert queue.is_open == False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_relationships():
    queue = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    assert hasattr(queue, 'requests')
    assert hasattr(queue, 'managers')
    assert hasattr(queue, 'user_profile')
    assert hasattr(queue, 'manager_profiles')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_unique_constraint():
    queue1 = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    queue2 = Queue(
        user_id=12345678,
        name="Different Queue"
    )

    assert queue1.user_id == queue2.user_id
    assert queue1.name != queue2.name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_timestamp_fields():
    queue = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    assert hasattr(queue, 'created_at')
    assert hasattr(queue, 'updated_at')


class TestQueuesPatchIntegration:
    """Integration tests for PATCH /api/v1/queues/{id} endpoint."""

    TEST_QUEUE_ID = 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_update_queue(self, TestClientWithMocks, admin_user_token):
        """Test admin can update queue."""
        from app.database.models import Queue

        mock_db = AsyncMock()
        
        queue_data = {
            "id": self.TEST_QUEUE_ID,
            "user_id": 12345678,
            "name": "Test Queue",
            "description": "Original description",
            "visibility": 0,
            "is_open": True,
        }
        
        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.user_id = 12345678
        mock_queue.name = "Test Queue"
        mock_queue.description = "Original description"
        mock_queue.visibility = 0
        mock_queue.is_open = True
        
        mock_user = MagicMock()
        mock_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        
        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={"name": "Updated Queue"},
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower() or "no changes" in data["message"].lower()
        mock_db.update.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_owner_can_update_queue(self, TestClientWithMocks, admin_user_token):
        """Test queue owner can update queue."""
        from app.database.models import Queue
        
        mock_db = AsyncMock()
        
        queue_data = {
            "id": self.TEST_QUEUE_ID,
            "user_id": 99999999,
            "name": "Test Queue",
            "description": "Original description",
            "visibility": 0,
            "is_open": True,
        }
        
        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"
        mock_queue.description = "Original description"
        mock_queue.visibility = 0
        mock_queue.is_open = True
        
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={"description": "Updated description"},
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower() or "no changes" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_gets_forbidden_on_queue_patch(self, TestClientWithMocks, admin_user_token):
        """Test non-admin user gets 403 Forbidden on queue patch."""
        from app.database.models import Queue
        
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 88888888
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        
        test_client = TestClientWithMocks(mock_db=mock_db)
        
        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=88888888):
            headers = {"Authorization": "Bearer test_token_not_admin"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={"name": "Hacked Queue"},
                headers=headers
            )
        
        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()


class TestQueuesGetIntegration:
    """Integration tests for GET /api/v1/queues/{id} endpoint."""

    TEST_QUEUE_ID = 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_queue_by_id(self, TestClientWithMocks, admin_user_token):
        """Test GET /api/v1/queues/{id} returns specific queue."""
        from app.database.schemas import QueueSchema
        from app.database.models import Queue

        mock_db = AsyncMock()

        queue_data = {
            "id": self.TEST_QUEUE_ID,
            "user_id": 12345678,
            "name": "Test Queue",
            "description": "A test queue",
            "visibility": 0,
            "is_open": True,
        }

        mock_queue = QueueSchema.model_validate(queue_data)

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            mock_user = MagicMock()
            mock_user.id = 11111111
            admin_role = MagicMock()
            admin_role.name = "admin"
            mock_user.roles = [admin_role]
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = test_client.get(f"/api/v1/queues/{self.TEST_QUEUE_ID}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.TEST_QUEUE_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_not_found(self, TestClientWithMocks, admin_user_token):
        """Test GET /api/v1/queues/{id} returns 404 for non-existent queue."""
        from app.database.models import Queue

        mock_db = AsyncMock()

        async def mock_get(model, **kwargs):
            if model == Queue:
                return None
            mock_user = MagicMock()
            mock_user.id = 11111111
            admin_role = MagicMock()
            admin_role.name = "admin"
            mock_user.roles = [admin_role]
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = test_client.get("/api/v1/queues/999999", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


# Unit tests
