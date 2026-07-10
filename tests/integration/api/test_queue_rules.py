"""
Integration tests for /queues/{queue_id}/rules endpoint.

Tests full CRUD operations for queue rules via the dedicated endpoint.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestQueueRulesCRUD:
    """Integration tests for queue rule CRUD operations."""

    TEST_QUEUE_ID = 1
    TEST_RULE_ID = 100
    TEST_USER_ID = 12345678

    @pytest.fixture
    def valid_rule_data(self):
        return {
            "type": "rate_limit",
            "config": {
                "max_requests": 5,
                "period": "week",
                "scope": "user",
            },
        }

    @pytest.fixture
    def another_valid_rule_data(self):
        return {
            "type": "cooldown",
            "config": {
                "cooldown_seconds": 3600,
                "scope": "user",
            },
        }

    def _make_mock_queue(self, queue_id=None, user_id=None):
        mock_queue = MagicMock()
        mock_queue.id = queue_id or self.TEST_QUEUE_ID
        mock_queue.user_id = user_id or self.TEST_USER_ID
        mock_queue.name = "Test Queue"
        mock_queue.is_open = True
        return mock_queue

    def _make_mock_rule(self, rule_id=None, queue_id=None, rule_type="rate_limit"):
        mock_rule = MagicMock()
        mock_rule.id = rule_id or self.TEST_RULE_ID
        mock_rule.queue_id = queue_id or self.TEST_QUEUE_ID
        mock_rule.type = rule_type
        mock_rule.config = {}
        mock_rule.is_active = True
        mock_rule.version = "1.0"
        return mock_rule

    def _make_mock_session(self, execute_result=None):
        class MockSession:
            async def __aenter__(self):
                sess = AsyncMock()
                if execute_result:
                    sess.execute = AsyncMock(return_value=execute_result)
                return sess
            async def __aexit__(self, *args):
                pass
        return MockSession

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_lists_rules(self, TestClientWithMocks, admin_user_token, valid_rule_data):
        """Test admin can list all rules for a queue."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rule]

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.session = self._make_mock_session(mock_result)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_gets_single_rule(self, TestClientWithMocks, admin_user_token):
        """Test admin can get a single rule by ID."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_rule

        mock_db = AsyncMock()
        mock_db.get.side_effect = [mock_queue, mock_rule]
        mock_db.session = self._make_mock_session(mock_result)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/{self.TEST_RULE_ID}",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.TEST_RULE_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_creates_rule(self, TestClientWithMocks, admin_user_token, valid_rule_data):
        """Test admin can create a new rule."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=valid_rule_data,
                headers=headers,
            )

        assert response.status_code == 201

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_updates_rule(self, TestClientWithMocks, admin_user_token):
        """Test admin can update an existing rule."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()

        mock_db = AsyncMock()
        mock_db.get.side_effect = [mock_queue, mock_rule]
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/{self.TEST_RULE_ID}",
                json={"is_active": False},
                headers=headers,
            )

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_deletes_rule(self, TestClientWithMocks, admin_user_token):
        """Test admin can delete a rule."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()

        mock_db = AsyncMock()
        mock_db.get.side_effect = [mock_queue, mock_rule]
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.delete(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/{self.TEST_RULE_ID}",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_replaces_all_rules(self, TestClientWithMocks, admin_user_token, valid_rule_data):
        """Test admin can replace all rules for a queue."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.put(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json={"rules": [valid_rule_data]},
                headers=headers,
            )

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_owner_manages_rules(self, TestClientWithMocks, admin_user_token, valid_rule_data):
        """Test queue owner can manage rules."""
        from app.database.models import Queue

        owner_id = 99999999
        mock_queue = self._make_mock_queue(user_id=owner_id)
        mock_rule = self._make_mock_rule()

        mock_db = AsyncMock()
        mock_db.get.side_effect = [mock_queue, mock_rule]
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=owner_id):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=valid_rule_data,
                headers=headers,
            )

        assert response.status_code == 201

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_owner_gets_forbidden(self, TestClientWithMocks, admin_user_token, valid_rule_data):
        """Test non-owner gets 403 when trying to manage rules."""
        from app.security import generate_token
        from app.database.models import Queue

        mock_queue = self._make_mock_queue(user_id=12345678)
        mock_user = MagicMock()
        mock_user.id = 88888888
        mock_user.roles = []

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_user
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=88888888):
            headers = {"Authorization": f"Bearer {generate_token(88888888)}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=valid_rule_data,
                headers=headers,
            )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_queue_returns_404(self, TestClientWithMocks, admin_user_token):
        """Test that accessing rules for a non-existent queue returns 404."""
        from app.database.models import Queue

        mock_db = AsyncMock()
        mock_db.get.return_value = None

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get(
                f"/api/v1/queues/999999/rules",
                headers=headers,
            )

        assert response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_rule_returns_404(self, TestClientWithMocks, admin_user_token):
        """Test that accessing a non-existent rule returns 404."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/999999",
                headers=headers,
            )

        assert response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_duplicate_rule_returns_409(self, TestClientWithMocks, admin_user_token, valid_rule_data):
        """Test that creating a duplicate rule returns 409 Conflict."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()
        existing_rule = self._make_mock_rule(rule_type="rate_limit")
        existing_rule.config = valid_rule_data["config"]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [existing_rule]

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.session = self._make_mock_session(mock_result)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=valid_rule_data,
                headers=headers,
            )

        assert response.status_code == 409

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_rule_config_returns_400(self, TestClientWithMocks, admin_user_token):
        """Test that submitting invalid rule config returns 400."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        invalid_data = {
            "type": "invalid_type",
            "config": {},
        }

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=invalid_data,
                headers=headers,
            )

        assert response.status_code == 400

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_patch_queue_no_longer_affects_rules(self, TestClientWithMocks, admin_user_token):
        """Test that PATCH /queues/{id} no longer accepts or modifies rules."""
        from app.database.models import Queue

        mock_queue = self._make_mock_queue()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_queue
        mock_db.update = AsyncMock()
        mock_db.session = self._make_mock_session()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch("app.security.decorators._get_authenticated_user_id", return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={
                    "name": "Updated Name",
                    "rules": [
                        {
                            "type": "rate_limit",
                            "config": {"max_requests": 10, "period": "day"},
                        }
                    ],
                },
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated" in data["message"].lower()
