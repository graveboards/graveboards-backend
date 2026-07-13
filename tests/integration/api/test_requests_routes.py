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
    def mock_rc(self):
        """Create a mock Redis client."""
        from unittest.mock import AsyncMock

        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.expire = AsyncMock(return_value=True)
        return mock_rc

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
    async def test_success_submits_request_and_queues_task(self, TestClientWithMocks, valid_request_body, mock_osu_client, security_disabled):
        """Test successful request submission that queues task for processing."""
        from app.redis.models import QueueRequestHandlerTask

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                sess.execute = AsyncMock(return_value=mock_result)
                return sess
            async def __aexit__(self, *args):
                pass

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
            None,
        ]
        mock_db.add = AsyncMock()
        mock_db.session = MockSession

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

        with patch('api.v1.requests.OsuAPIClient', return_value=mock_osu_client):
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
            http_request_id="",
        )
        assert int(data["task_id"]) == expected_task.hashed_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_not_found(self, TestClientWithMocks, valid_request_body, security_disabled):
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
    async def test_queue_closed(self, TestClientWithMocks, valid_request_body, security_disabled):
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
    async def test_duplicate_request(self, TestClientWithMocks, valid_request_body, security_disabled):
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
    async def test_task_already_processing(self, TestClientWithMocks, valid_request_body, mock_osu_client, security_disabled):
        """Test request submission fails when task is already processing."""
        from app.redis.models import QueueRequestHandlerTask

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                sess.execute = AsyncMock(return_value=MagicMock())
                return sess
            async def __aexit__(self, *args):
                pass

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
        ]
        mock_db.add = AsyncMock()
        mock_db.session = MockSession

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
            http_request_id="",
        )

        mock_osu_client.rc = mock_rc

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {
                "id": self.TEST_BEATMAPSET_ID,
                "status": "wip",
            }

        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch('api.v1.requests.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 409
        data = response.json()
        assert f"The request with beatmapset ID '{self.TEST_BEATMAPSET_ID}' in queue '{mock_queue.name}' is currently being processed" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_already_processing_but_failed(self, TestClientWithMocks, valid_request_body, mock_osu_client, security_disabled):
        """Test request submission succeeds when previous task failed."""
        from app.redis.models import QueueRequestHandlerTask

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                sess.execute = AsyncMock(return_value=MagicMock())
                return sess
            async def __aexit__(self, *args):
                pass

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
        ]
        mock_db.add = AsyncMock()
        mock_db.session = MockSession

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

        with patch('api.v1.requests.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert data["message"] == "Request submitted and queued for processing!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClientWithMocks, valid_request_body, mock_osu_client, security_disabled):
        """Test security disabled bypasses authorization."""
        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                sess.execute = AsyncMock(return_value=MagicMock())
                return sess
            async def __aexit__(self, *args):
                pass

        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            mock_queue,
            None,
            None,
        ]
        mock_db.add = AsyncMock()
        mock_db.session = MockSession

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

        with patch('api.v1.requests.OsuAPIClient', return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 202

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_can_get_own_requests(self, TestClientWithMocks, admin_user_token):
        """Test that user can get their own requests."""
        from app.database.schemas import RequestSchema

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

        with patch('app.security.decorators._get_authenticated_user_id', return_value=12345678):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_gets_forbidden_on_other_users_requests(self, TestClientWithMocks):
        """Test that user gets 403 Forbidden on other users' requests."""
        from app.security import generate_token
        from app.database.schemas import RequestSchema

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

        with patch('app.security.decorators._get_authenticated_user_id', return_value=12345678):
            headers = {"Authorization": f"Bearer {generate_token(12345678)}"}
            response = test_client.get("/api/v1/requests", headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_get_all_requests(self, TestClientWithMocks, admin_user_token):
        """Test that admin can get all requests."""
        from app.database.schemas import RequestSchema

        mock_db = AsyncMock()

        admin_request_data = {
            "id": 1,
            "user_id": 99999999,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_admin_request = RequestSchema.model_validate(admin_request_data)

        user_request_data = {
            "id": 2,
            "user_id": 12345678,
            "beatmapset_id": 35966,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        mock_user_request = RequestSchema.model_validate(user_request_data)

        mock_db.get_many = AsyncMock(return_value=[mock_admin_request, mock_user_request])

        mock_user = MagicMock()
        mock_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        mock_db.get = AsyncMock(return_value=mock_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_request_by_id(self, TestClientWithMocks, admin_user_token):
        """Test GET /api/v1/requests/{id} returns specific request."""
        from app.security import decode_token
        from app.database.schemas import RequestSchema
        from app.database.models import Request

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
        
        decoded_token = decode_token(admin_user_token)
        user_id = int(decoded_token["sub"])
        mock_user = MagicMock()
        mock_user.id = user_id
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        
        async def mock_get(model, **kwargs):
            if model.__name__ == "Request":
                return mock_request
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=user_id), \
             patch('app.security.decorators.ownership_authorization', lambda *args, **kwargs: lambda f: f):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests/1", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_request_not_found(self, TestClientWithMocks, admin_user_token):
        """Test GET /api/v1/requests/{id} returns 404 for non-existent request."""
        from app.database.models import Request

        mock_db = AsyncMock()

        async def mock_get(model, **kwargs):
            if model == Request:
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
        response = test_client.get("/api/v1/requests/999999", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRequestsPatchIntegration:
    """Integration tests for PATCH /api/v1/requests/{id} endpoint."""

    TEST_REQUEST_ID = 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_update_request_status(self, TestClientWithMocks, admin_user_token):
        """Test admin can update request status."""
        from app.database.schemas import RequestSchema
        from app.database.models import Request

        mock_db = AsyncMock()
        
        request_data = {
            "id": self.TEST_REQUEST_ID,
            "user_id": 12345678,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        
        mock_request = RequestSchema.model_validate(request_data)
        
        mock_user = MagicMock()
        mock_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        
        async def mock_get(model, **kwargs):
            if model == Request:
                return mock_request
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/requests/{self.TEST_REQUEST_ID}",
                json={"status": 1},
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()
        mock_db.update.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_gets_forbidden_on_request_patch(self, TestClientWithMocks, admin_user_token):
        """Test non-admin user gets 403 Forbidden on request patch."""
        from app.security import generate_token

        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
            headers = {"Authorization": f"Bearer {generate_token(99999999)}"}
            response = test_client.patch(
                f"/api/v1/requests/{self.TEST_REQUEST_ID}",
                json={"status": 1},
                headers=headers
            )

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_owner_can_update_request_via_override(self, TestClientWithMocks, admin_user_token):
        """Test queue owner can update request via override."""
        from app.database.schemas import RequestSchema
        from app.database.models import Request, Queue

        mock_db = AsyncMock()
        
        request_data = {
            "id": self.TEST_REQUEST_ID,
            "user_id": 12345678,
            "beatmapset_id": 35965,
            "queue_id": 1,
            "status": 0,
            "mv_checked": False,
        }
        
        mock_request = RequestSchema.model_validate(request_data)
        mock_request.queue = MagicMock()
        mock_request.queue.user_id = 99999999
        
        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            if model == Request:
                if kwargs.get("id") == self.TEST_REQUEST_ID:
                    if kwargs.get("_include", {}).get("queue"):
                        return mock_request
                    return mock_request
            elif model == Queue:
                return mock_queue
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/requests/{self.TEST_REQUEST_ID}",
                json={"status": 1},
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()


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


class TestRequestsTasksIntegration:
    """Integration tests for GET /api/v1/requests/tasks endpoints."""

    TEST_QUEUE_ID = 1
    TEST_BEATMAPSET_ID = 35965
    TEST_USER_ID = 12345678

    @pytest.fixture
    def mock_rc_with_task(self):
        """Create a mock Redis client with a task."""
        from unittest.mock import AsyncMock
        from app.redis.models import QueueRequestHandlerTask

        task = QueueRequestHandlerTask(
            user_id=self.TEST_USER_ID,
            beatmapset_id=self.TEST_BEATMAPSET_ID,
            queue_id=self.TEST_QUEUE_ID,
            comment="Please rank this beatmapset!",
            mv_checked=False,
            http_request_id="",
        )

        mock_rc = AsyncMock()
        mock_rc.paginate_scan = AsyncMock(return_value=[f"QUEUE_REQUEST_HANDLER_TASK:{task.hashed_id}"])
        mock_rc.hgetall = AsyncMock(return_value=task.serialize())

        return mock_rc

    @pytest.fixture
    def admin_user(self):
        """Create a mock admin user."""
        from unittest.mock import MagicMock
        from app.database.enums import RoleName

        mock_user = MagicMock()
        mock_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value
        mock_user.roles = [admin_role]

        return mock_user

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_get_all_tasks(self, TestClientWithMocks, admin_user_token, mock_rc_with_task, admin_user):
        """Test GET /api/v1/requests/tasks returns all tasks."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=admin_user)

        test_client = TestClientWithMocks(mock_rc=mock_rc_with_task, mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests/tasks", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["user_id"] == self.TEST_USER_ID
        assert data[0]["beatmapset_id"] == self.TEST_BEATMAPSET_ID
        assert data[0]["queue_id"] == self.TEST_QUEUE_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_get_all_tasks_empty(self, TestClientWithMocks, admin_user_token, admin_user):
        """Test GET /api/v1/requests/tasks returns empty list when no tasks exist."""
        mock_rc = AsyncMock()
        mock_rc.paginate_scan = AsyncMock(return_value=[])

        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=admin_user)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests/tasks", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_get_task_by_hashed_id(self, TestClientWithMocks, admin_user_token, mock_rc_with_task):
        """Test GET /api/v1/requests/tasks/{hashed_id} returns specific task."""
        test_client = TestClientWithMocks(mock_rc=mock_rc_with_task)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests/tasks/12345", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == self.TEST_USER_ID
        assert data["beatmapset_id"] == self.TEST_BEATMAPSET_ID
        assert data["queue_id"] == self.TEST_QUEUE_ID
        assert data["comment"] == "Please rank this beatmapset!"
        assert data["mv_checked"] is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_not_found(self, TestClientWithMocks, admin_user_token):
        """Test 404 when task doesn't exist."""
        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)

        test_client = TestClientWithMocks(mock_rc=mock_rc)

        with patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get("/api/v1/requests/tasks/999999", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_user_gets_forbidden(self, TestClientWithMocks):
        """Test that non-admin user gets 403 Forbidden on task endpoints."""
        from app.security import generate_token

        test_client = TestClientWithMocks()

        with patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
            headers = {"Authorization": f"Bearer {generate_token(99999999)}"}
            response = test_client.get("/api/v1/requests/tasks", headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()
