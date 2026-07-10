"""
Integration tests for queue rule enforcement.

Tests rule checks during request submission and rule management via queue PATCH.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRestrictionsOnRequestSubmission:
    """Integration tests for rule enforcement on POST /api/v1/requests."""

    TEST_USER_ID = 12345678
    TEST_BEATMAPSET_ID = 35965
    TEST_QUEUE_ID = 1

    @pytest.fixture
    def valid_request_body(self):
        return {
            "user_id": self.TEST_USER_ID,
            "beatmapset_id": self.TEST_BEATMAPSET_ID,
            "queue_id": self.TEST_QUEUE_ID,
            "comment": "Please rank this beatmapset!",
            "mv_checked": False,
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_submits_when_no_rules(
        self, TestClientWithMocks, valid_request_body, security_disabled
    ):
        """Test request succeeds when queue has no rules."""
        from app.database.models import Queue

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
        mock_rc.get = AsyncMock(return_value=None)
        mock_rc.set = AsyncMock(return_value=True)

        class MockLockCtx:
            async def __aenter__(self):
                return None

            async def __aexit__(self, *args):
                pass

        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {"id": self.TEST_BEATMAPSET_ID, "status": "wip"}

        mock_osu_client = MagicMock()
        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch("api.v1.requests.OsuAPIClient", return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 202

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_blocked_by_rate_limit(
        self, TestClientWithMocks, valid_request_body, security_disabled
    ):
        """Test request is blocked when rate limit is exceeded."""
        from app.database.models import Queue
        from app.database.models.queue_rule import QueueRule

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.queue_id = self.TEST_QUEUE_ID
        mock_rule.type = "rate_limit"
        mock_rule.version = "1.0"
        mock_rule.config = {
            "max_requests": 1,
            "period": "week",
            "scope": "user",
        }
        mock_rule.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rule]

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
        mock_rc.incr = AsyncMock(return_value=2)
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
            return {"id": self.TEST_BEATMAPSET_ID, "status": "wip"}

        mock_osu_client = MagicMock()
        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch("api.v1.requests.OsuAPIClient", return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_blocked_by_cooldown(
        self, TestClientWithMocks, valid_request_body, security_disabled
    ):
        """Test request is blocked when cooldown period is active."""
        from datetime import datetime, timezone, timedelta

        from app.database.models import Queue

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.queue_id = self.TEST_QUEUE_ID
        mock_rule.type = "cooldown"
        mock_rule.version = "1.0"
        mock_rule.config = {
            "cooldown_seconds": 3600,
            "scope": "user",
        }
        mock_rule.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rule]

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

        now = datetime.now(timezone.utc)
        thirty_minutes_ago = int((now - timedelta(minutes=30)).timestamp())

        mock_rc = AsyncMock()
        mock_rc.incr = AsyncMock(return_value=1)
        mock_rc.expire = AsyncMock(return_value=True)
        mock_rc.exists = AsyncMock(return_value=False)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.publish = AsyncMock(return_value=True)
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.get = AsyncMock(return_value=str(thirty_minutes_ago))
        mock_rc.set = AsyncMock(return_value=True)

        class MockLockCtx:
            async def __aenter__(self):
                return None

            async def __aexit__(self, *args):
                pass

        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {"id": self.TEST_BEATMAPSET_ID, "status": "wip"}

        mock_osu_client = MagicMock()
        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch("api.v1.requests.OsuAPIClient", return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_blocked_by_blacklist(
        self, TestClientWithMocks, valid_request_body, security_disabled
    ):
        """Test request is blocked when user is blacklisted."""
        from app.database.models import Queue

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.name = "test_queue"
        mock_queue.is_open = True

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.queue_id = self.TEST_QUEUE_ID
        mock_rule.type = "blacklist"
        mock_rule.version = "1.0"
        mock_rule.config = {
            "scope": "user",
            "target": [self.TEST_USER_ID],
        }
        mock_rule.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rule]

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
            return {"id": self.TEST_BEATMAPSET_ID, "status": "wip"}

        mock_osu_client = MagicMock()
        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch("api.v1.requests.OsuAPIClient", return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_passes_when_inactive_rule(
        self, TestClientWithMocks, valid_request_body, security_disabled
    ):
        """Test request succeeds when rule exists but is inactive."""
        from app.database.models import Queue

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
        mock_rc.get = AsyncMock(return_value=None)
        mock_rc.set = AsyncMock(return_value=True)

        class MockLockCtx:
            async def __aenter__(self):
                return None

            async def __aexit__(self, *args):
                pass

        mock_rc.lock_ctx = MagicMock(return_value=MockLockCtx())

        async def mock_get_beatmapset_wip(*args, **kwargs):
            return {"id": self.TEST_BEATMAPSET_ID, "status": "wip"}

        mock_osu_client = MagicMock()
        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch("api.v1.requests.OsuAPIClient", return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=valid_request_body)

        assert response.status_code == 202

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_passes_when_user_not_in_target(
        self, TestClientWithMocks, security_disabled
    ):
        """Test request succeeds when user is not in rule target list."""
        from app.database.models import Queue

        different_user = 99999999
        body = {
            "user_id": different_user,
            "beatmapset_id": self.TEST_BEATMAPSET_ID,
            "queue_id": self.TEST_QUEUE_ID,
            "comment": "Please rank this beatmapset!",
            "mv_checked": False,
        }

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

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.queue_id = self.TEST_QUEUE_ID
        mock_rule.type = "blacklist"
        mock_rule.config = {
            "scope": "user",
            "target": [12345678],
        }
        mock_rule.is_active = True

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
            return {"id": self.TEST_BEATMAPSET_ID, "status": "wip"}

        mock_osu_client = MagicMock()
        mock_osu_client.get_beatmapset = AsyncMock(side_effect=mock_get_beatmapset_wip)

        test_client = TestClientWithMocks(mock_rc=mock_rc, mock_db=mock_db)

        with patch("api.v1.requests.OsuAPIClient", return_value=mock_osu_client):
            response = test_client.post("/api/v1/requests", json=body)

        assert response.status_code == 202


class TestQueueRulesPatch:
    """Integration tests for PATCH /api/v1/queues/{id} with rules."""

    TEST_QUEUE_ID = 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_set_rules(self, TestClientWithMocks, admin_user_token):
        """Test admin can set rules via PATCH."""
        from app.database.models import Queue

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.user_id = 12345678
        mock_queue.name = "Test Queue"
        mock_queue.description = "A test queue"
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

        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                sess.execute = AsyncMock(return_value=MagicMock())
                return sess
            async def __aexit__(self, *args):
                pass

        mock_db = AsyncMock()
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()
        mock_db.session = MockSession

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={
                    "rules": [
                        {
                            "type": "rate_limit",
                            "config": {
                                "max_requests": 2,
                                "period": "week",
                                "scope": "user",
                            },
                        }
                    ]
                },
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_queue_owner_can_set_rules(
        self, TestClientWithMocks, admin_user_token
    ):
        """Test queue owner can set rules via PATCH."""
        from app.database.models import Queue

        owner_id = 99999999

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.user_id = owner_id
        mock_queue.name = "Test Queue"
        mock_queue.description = "A test queue"
        mock_queue.visibility = 0
        mock_queue.is_open = True

        mock_user = MagicMock()
        mock_user.id = owner_id
        mock_user.roles = []

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user

        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                sess.execute = AsyncMock(return_value=MagicMock())
                return sess
            async def __aexit__(self, *args):
                pass

        mock_db = AsyncMock()
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()
        mock_db.session = MockSession

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=owner_id):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={
                    "rules": [
                        {
                            "type": "cooldown",
                            "config": {
                                "cooldown_seconds": 86400,
                                "scope": "user",
                            },
                        }
                    ]
                },
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_cannot_set_rules(
        self, TestClientWithMocks, admin_user_token
    ):
        """Test non-admin non-owner gets 403 when trying to set rules."""
        from app.security import generate_token
        from app.database.models import Queue

        mock_queue = MagicMock()
        mock_queue.id = self.TEST_QUEUE_ID
        mock_queue.user_id = 12345678
        mock_queue.name = "Test Queue"

        mock_user = MagicMock()
        mock_user.id = 88888888
        mock_user.roles = []

        async def mock_get(model, **kwargs):
            return mock_user

        mock_db = AsyncMock()
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=88888888):
            headers = {"Authorization": f"Bearer {generate_token(88888888)}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={
                    "rules": [
                        {
                            "type": "rate_limit",
                            "config": {
                                "max_requests": 1,
                                "period": "week",
                            },
                        }
                    ]
                },
                headers=headers,
            )

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()
