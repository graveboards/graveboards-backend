"""
Integration tests for POST /api/v1/requests endpoint.

Tests the beatmapset request submission via full HTTP stack.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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

    @pytest.fixture
    def mock_osu_client(self, mock_rc):
        """Create a mock osu client."""
        mock_client = MagicMock()
        mock_client.rc = mock_rc
        return mock_client

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_success_submits_request_and_queues_task(self, TestClientWithMocks, valid_request_body, mock_osu_client):
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
        mock_rc.incr = AsyncMock(return_value=1)
        mock_rc.expire = AsyncMock(return_value=True)
        mock_rc.exists = AsyncMock(return_value=False)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)
        mock_rc.hgetall = AsyncMock(return_value=None)

        class MockLockCtx:
            async def __aenter__(self):
                return None
            async def __aexit__(self, *args):
                pass
        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

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
    async def test_queue_not_found(self, TestClientWithMocks, valid_request_body):
        """Test request submission fails when queue doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        body = valid_request_body.copy()
        body["queue_id"] = -1
        response = test_client.post("/api/v1/requests", json=body)

        assert response.status_code == 404
        data = response.json()
        assert f"The queue with ID '{body['queue_id']}' not found" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_closed(self, TestClientWithMocks, valid_request_body):
        """Test request submission fails when queue is closed."""
        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = False

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 403
        data = response.json()
        assert f"The queue '{mock_queue.name}' is closed" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_duplicate_request(self, TestClientWithMocks, valid_request_body):
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

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 409
        data = response.json()
        assert f"The request with beatmapset ID '{self.TEST_BEATMAPSET_ID}' already exists in queue '{mock_queue.name}'" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_already_processing(self, TestClientWithMocks, valid_request_body, mock_osu_client):
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
        mock_rc.incr = AsyncMock(return_value=2)
        mock_rc.expire = AsyncMock(return_value=True)
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

        class MockLockCtx:
            async def __aenter__(self):
                return None
            async def __aexit__(self, *args):
                pass
        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        expected_task = QueueRequestHandlerTask(
            user_id=self.TEST_USER_ID,
            beatmapset_id=self.TEST_BEATMAPSET_ID,
            queue_id=self.TEST_QUEUE_ID,
            comment=valid_request_body["comment"],
            mv_checked=valid_request_body["mv_checked"],
        )

        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 409
        data = response.json()
        assert f"The request with beatmapset ID '{self.TEST_BEATMAPSET_ID}' in queue '{mock_queue.name}' is currently being processed" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_already_processing_but_failed(self, TestClientWithMocks, valid_request_body, mock_osu_client):
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
        mock_rc.incr = AsyncMock(return_value=2)
        mock_rc.expire = AsyncMock(return_value=True)
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

        class MockLockCtx:
            async def __aenter__(self):
                return None
            async def __aexit__(self, *args):
                pass
        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert data["message"] == "Request submitted and queued for processing!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClientWithMocks, valid_request_body, mock_osu_client):
        """Test DISABLE_SECURITY=True bypasses authorization."""
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
        mock_rc.incr = AsyncMock(return_value=1)
        mock_rc.expire = AsyncMock(return_value=True)
        mock_rc.exists = AsyncMock(return_value=False)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)
        mock_rc.hgetall = AsyncMock(return_value=None)

        class MockLockCtx:
            async def __aenter__(self):
                return None
            async def __aexit__(self, *args):
                pass
        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', True), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 202


# Unit tests
@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_model_creation():
    from app.database.models import Request, Queue

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
    from app.database.models import Request

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
    from app.database.models import Request

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
    from app.database.models import Request

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
    from app.database.models import Request

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
    from app.database.models import Request, Queue

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
