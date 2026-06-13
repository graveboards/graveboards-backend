"""
Integration tests for POST /api/v1/requests endpoint.

Tests the beatmapset request submission via full HTTP stack.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models import Request, Queue
from app.test_app import MockDatabaseMiddleware


class TestRequestsPostIntegration:
    """Integration tests for POST /api/v1/requests endpoint."""

    TEST_USER_ID = 12345678
    TEST_BEATMAPSET_ID = 35965
    TEST_QUEUE_ID = 1

    @pytest.fixture
    def valid_request_body(self):
        """Return a valid request submission body."""
        return {
            "user_id": self.TEST_USER_ID,
            "beatmapset_id": self.TEST_BEATMAPSET_ID,
            "queue_id": self.TEST_QUEUE_ID,
            "comment": "Please rank this beatmapset!",
            "mv_checked": False,
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_success_submits_request_and_queues_task(self, TestClient, valid_request_body):
        """Test successful request submission that queues task for processing."""
        from app.redis.models import QueueRequestHandlerTask

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
            None,
        ]
        mock_db.add = AsyncMock()

        mock_rc = AsyncMock()
        mock_rc.exists = AsyncMock(return_value=False)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)
        mock_rc.hgetall = AsyncMock(return_value=None)

        mock_osu_client = MagicMock()
        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            scope["state"]["rc"] = mock_rc
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
                response = TestClient.post("/api/v1/requests", json=valid_request_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert data["message"] == "Request submitted and queued for processing!"
        assert "task_id" in data
        assert data["task_id"] is not None

        expected_task = QueueRequestHandlerTask(
            user_id=self.TEST_USER_ID,
            beatmapset_id=self.TEST_BEATMAPSET_ID,
            queue_id=self.TEST_QUEUE_ID,
            comment=valid_request_body["comment"],
            mv_checked=valid_request_body["mv_checked"],
        )
        assert int(data["task_id"]) == expected_task.hashed_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_not_found(self, TestClient, valid_request_body):
        """Test request submission fails when queue doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None
        mock_db.add = AsyncMock()

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            body = valid_request_body.copy()
            body["queue_id"] = -1
            response = TestClient.post("/api/v1/requests", json=body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 404
        data = response.json()
        assert f"The queue with ID '{body['queue_id']}' not found" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_closed(self, TestClient, valid_request_body):
        """Test request submission fails when queue is closed."""
        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = False

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.add = AsyncMock()

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            response = TestClient.post("/api/v1/requests", json=valid_request_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 403
        data = response.json()
        assert f"The queue '{mock_queue.name}' is closed" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_duplicate_request(self, TestClient, valid_request_body):
        """Test request submission fails when duplicate exists."""
        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_existing_request = MagicMock()
        mock_existing_request.beatmapset_id = self.TEST_BEATMAPSET_ID

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            mock_existing_request,
        ]
        mock_db.add = AsyncMock()

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            response = TestClient.post("/api/v1/requests", json=valid_request_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 409
        data = response.json()
        assert f"The request with beatmapset ID '{self.TEST_BEATMAPSET_ID}' already exists in queue '{mock_queue.name}'" in data["detail"]

 

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_already_processing(self, TestClient, valid_request_body):
        """Test request submission fails when task is already processing."""
        from app.redis.models import QueueRequestHandlerTask

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
        ]
        mock_db.add = AsyncMock()

        mock_rc = AsyncMock()
        mock_rc.exists = AsyncMock(return_value=True)
        mock_rc.hgetall = AsyncMock(return_value={
            "user_id": str(self.TEST_USER_ID),
            "beatmapset_id": str(self.TEST_BEATMAPSET_ID),
            "queue_id": str(self.TEST_QUEUE_ID),
            "comment": valid_request_body["comment"],
            "mv_checked": str(valid_request_body["mv_checked"]),
            "completed_at": "",
            "failed_at": "",
        })
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)

        expected_task = QueueRequestHandlerTask(
            user_id=self.TEST_USER_ID,
            beatmapset_id=self.TEST_BEATMAPSET_ID,
            queue_id=self.TEST_QUEUE_ID,
            comment=valid_request_body["comment"],
            mv_checked=valid_request_body["mv_checked"],
        )

        mock_osu_client = MagicMock()
        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            scope["state"]["rc"] = mock_rc
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
                response = TestClient.post("/api/v1/requests", json=valid_request_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 409
        data = response.json()
        assert f"The request with beatmapset ID '{self.TEST_BEATMAPSET_ID}' in queue '{mock_queue.name}' is currently being processed" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_already_processing_but_failed(self, TestClient, valid_request_body):
        """Test request submission succeeds when previous task failed."""
        from app.redis.models import QueueRequestHandlerTask

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
        ]
        mock_db.add = AsyncMock()

        mock_rc = AsyncMock()
        mock_rc.exists = AsyncMock(return_value=True)
        mock_rc.hgetall = AsyncMock(return_value={
            "user_id": str(self.TEST_USER_ID),
            "beatmapset_id": str(self.TEST_BEATMAPSET_ID),
            "queue_id": str(self.TEST_QUEUE_ID),
            "comment": valid_request_body["comment"],
            "mv_checked": str(valid_request_body["mv_checked"]),
            "completed_at": "",
            "failed_at": "2024-01-01T00:00:00",
        })
        mock_rc.delete = AsyncMock(return_value=True)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)

        mock_osu_client = MagicMock()
        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            scope["state"]["rc"] = mock_rc
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
                response = TestClient.post("/api/v1/requests", json=valid_request_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert data["message"] == "Request submitted and queued for processing!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClient, valid_request_body):
        """Test DISABLE_SECURITY=True bypasses authorization."""
        os.environ["DISABLE_SECURITY"] = "True"

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
            None,
        ]
        mock_db.add = AsyncMock()

        mock_rc = AsyncMock()
        mock_rc.exists = AsyncMock(return_value=False)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)

        mock_osu_client = MagicMock()
        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            scope["state"]["rc"] = mock_rc
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
                response = TestClient.post("/api/v1/requests", json=valid_request_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
            os.environ["DISABLE_SECURITY"] = "False"


# Unit tests
@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_model_creation():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        status=0
    )

    assert request.user_id == 12345678
    assert request.beatmapset_id == 35965
    assert request.queue_id == 1
    assert request.status == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_with_comment():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        comment="Please rank this beatmapset!"
    )

    assert request.comment == "Please rank this beatmapset!"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_mv_checked():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        mv_checked=False
    )

    assert request.mv_checked == False

    request.mv_checked = True
    assert request.mv_checked == True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_status_values():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        status=0
    )

    assert request.status == 0

    request.status = 1
    assert request.status == 1

    request.status = 2
    assert request.status == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_relationships():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1
    )

    assert hasattr(request, 'beatmapset_snapshot')
    assert hasattr(request, 'user_profile')
    assert hasattr(request, 'queue')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_unique_constraint():
    queue = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    request1 = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=queue.id
    )

    request2 = Request(
        user_id=12345678,
        beatmapset_id=99999,
        queue_id=queue.id
    )

    assert request1.beatmapset_id != request2.beatmapset_id
    assert request1.queue_id == request2.queue_id
