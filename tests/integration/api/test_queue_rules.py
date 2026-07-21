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
    ADMIN_USER_ID = 11111111

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
        """Create a mock rule with proper attribute values (not MagicMock)."""
        from dataclasses import dataclass, field
        from datetime import datetime
        
        @dataclass
        class MockRule:
            id: int
            queue_id: int
            type: str
            config: dict
            is_active: bool
            version: str
            is_public: bool
            updated_at: datetime = field(default_factory=lambda: datetime.now())
            created_at: datetime = field(default_factory=lambda: datetime.now())
        
        return MockRule(
            id=rule_id or self.TEST_RULE_ID,
            queue_id=queue_id or self.TEST_QUEUE_ID,
            type=rule_type,
            config={},
            is_active=True,
            version="1.0",
            is_public=True,
        )

    def _make_mock_user(self, user_id, roles=None):
        """Create a mock user with the given roles."""
        mock_user = MagicMock()
        mock_user.id = user_id
        if roles is None:
            mock_user.roles = []
        else:
            mock_user.roles = roles
        return mock_user

    def _make_role(self, role_name):
        """Create a mock role with the given name string."""
        role = MagicMock()
        role.name = role_name
        return role

    def _make_mock_db(self, queue=None, user=None):
        """Create a mock DB with proper session mocking."""
        # Create a proper async context manager for the session
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=False)
        
        mock_db = AsyncMock()
        if queue and user:
            from app.database.models import Queue, User
            mock_db.get = AsyncMock(side_effect=lambda model, *args, **kwargs: 
                queue if model == Queue else (user if model == User else None))
        elif user:
            from app.database.models import User
            mock_db.get = AsyncMock(side_effect=lambda model, *args, **kwargs: 
                user if model == User else None)
        elif queue:
            from app.database.models import Queue
            mock_db.get = AsyncMock(side_effect=lambda model, *args, **kwargs: 
                queue if model == Queue else None)
        else:
            mock_db.get.return_value = None
        
        # session should return an async context manager, not a coroutine
        mock_db.session = MagicMock(return_value=mock_session_instance)
        return mock_db

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_lists_rules(self, TestClientWithMocks, admin_user_token, valid_rule_data, authenticated_user_id):
        """Test admin can list all rules for a queue."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.get_rules = AsyncMock(return_value=[mock_rule])

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
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
    async def test_admin_gets_single_rule(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test admin can get a single rule by ID."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.get_rule = AsyncMock(return_value=mock_rule)

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
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
    async def test_admin_creates_rule(self, TestClientWithMocks, admin_user_token, valid_rule_data, authenticated_user_id):
        """Test admin can create a new rule."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.get_rules = AsyncMock(return_value=[])
        mock_created_rule = self._make_mock_rule()
        mock_crud.create_rule = AsyncMock(return_value=mock_created_rule)

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.post(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                    json=valid_rule_data,
                    headers=headers,
                )

            assert response.status_code == 201

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_updates_rule(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test admin can update an existing rule."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.update_rule = AsyncMock(return_value=mock_rule)

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.patch(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/{self.TEST_RULE_ID}",
                    json={"config": {"cooldown_seconds": 7200}},
                    headers=headers,
                )

            assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_deletes_rule(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test admin can delete a rule."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_rule = self._make_mock_rule()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.delete_rule = AsyncMock(return_value=mock_rule)

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.delete(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/{self.TEST_RULE_ID}",
                    headers=headers,
                )

            assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_replaces_all_rules(self, TestClientWithMocks, admin_user_token, valid_rule_data, authenticated_user_id):
        """Test admin can replace all rules for a queue."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.upsert_rules = AsyncMock(return_value=[])

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.put(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                    json={"rules": [valid_rule_data]},
                    headers=headers,
                )

            assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_owner_manages_rules(self, TestClientWithMocks, admin_user_token, valid_rule_data, authenticated_user_id):
        """Test queue owner can manage rules."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue(user_id=self.TEST_USER_ID)
        mock_owner_user = self._make_mock_user(
            self.TEST_USER_ID,
            roles=[]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.get_rules = AsyncMock(return_value=[])
        mock_created_rule = self._make_mock_rule()
        mock_crud.create_rule = AsyncMock(return_value=mock_created_rule)

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_owner_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.TEST_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.post(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                    json=valid_rule_data,
                    headers=headers,
                )

            assert response.status_code == 201

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_owner_gets_forbidden(self, TestClientWithMocks, admin_user_token, valid_rule_data, authenticated_user_id):
        """Test non-owner non-admin gets 403."""
        mock_queue = self._make_mock_queue(user_id=self.TEST_USER_ID)
        mock_other_user = self._make_mock_user(
            99999999,
            roles=[]
        )

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_other_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(99999999):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=valid_rule_data,
                headers=headers,
            )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_queue_returns_404(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test 404 when queue doesn't exist."""
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_db = self._make_mock_db(user=mock_admin_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(self.ADMIN_USER_ID):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.get(
                f"/api/v1/queues/999999/rules",
                headers=headers,
            )

        assert response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_rule_returns_404(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test 404 when rule doesn't exist."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.get_rule = AsyncMock(return_value=None)

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.get(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules/999999",
                    headers=headers,
                )

            assert response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_duplicate_rule_returns_409(self, TestClientWithMocks, admin_user_token, valid_rule_data, authenticated_user_id):
        """Test 409 when duplicate rule exists."""
        from app.database.crud.rules import RuleCRUD

        mock_queue = self._make_mock_queue()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        existing_rule = self._make_mock_rule(rule_type=valid_rule_data["type"])
        existing_rule.config = valid_rule_data["config"]

        mock_crud = MagicMock(spec=RuleCRUD)
        mock_crud.get_rules = AsyncMock(return_value=[existing_rule])
        # Make create_rule raise Conflict to simulate duplicate detection
        from app.exceptions import Conflict
        async def mock_create_rule(*args, **kwargs):
            raise Conflict("Duplicate rule")
        mock_crud.create_rule = mock_create_rule

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        with patch('api.v1.queues.rules.RuleCRUD', return_value=mock_crud):
            test_client = TestClientWithMocks(mock_db=mock_db)

            with authenticated_user_id(self.ADMIN_USER_ID):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                response = test_client.post(
                    f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                    json=valid_rule_data,
                    headers=headers,
                )

            assert response.status_code == 409

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_rule_config_returns_400(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test 400 when rule config is invalid."""
        mock_queue = self._make_mock_queue()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)

        test_client = TestClientWithMocks(mock_db=mock_db)

        invalid_data = {"type": "invalid_type"}

        with authenticated_user_id(self.ADMIN_USER_ID):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}/rules",
                json=invalid_data,
                headers=headers,
            )

        assert response.status_code == 400

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_patch_queue_no_longer_affects_rules(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Test that patching queue doesn't affect rules."""
        mock_queue = self._make_mock_queue()
        mock_admin_user = self._make_mock_user(
            self.ADMIN_USER_ID,
            roles=[self._make_role("admin")]
        )

        mock_db = self._make_mock_db(queue=mock_queue, user=mock_admin_user)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(self.ADMIN_USER_ID):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/queues/{self.TEST_QUEUE_ID}",
                json={
                    "name": "Updated Name",
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
