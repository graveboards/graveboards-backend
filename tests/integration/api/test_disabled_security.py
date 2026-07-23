"""
Integration tests for security configuration.

Tests verify that security decorators work correctly with the
get_security_enabled() configuration mechanism. Disabling security no longer
skips authorization entirely - it resolves a dev identity (DEV_ADMIN_USER_ID
by default, or whatever the X-Debug-User-Id header requests) and runs the
same role/ownership checks against it that a real request would go through.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestSecurityConfiguration:
    """Test security decorator behavior with configuration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_by_default(self, TestClientWithMocks, admin_user_token, authenticated_user_id):
        """Verify security is enabled by default in test environment."""
        from app.database.models import Queue

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_still_enforces_roles_for_default_identity(
        self, TestClientWithMocks, security_disabled
    ):
        """Disabling security resolves the default dev identity (DEV_ADMIN_USER_ID)
        instead of a real login, but the role check still runs for real - if that
        identity isn't admin-roled in the DB, a non-owner PATCH is still rejected.
        """
        from app.database.models import Queue

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.roles = []

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.patch("/api/v1/queues/1", json={"name": "Updated"})

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_allows_admin_dev_identity(self, TestClientWithMocks, security_disabled):
        """The default dev identity (DEV_ADMIN_USER_ID) is admin-roled in a real
        seeded dev DB, so role-gated endpoints succeed with no auth header at all -
        the "just works" dev experience DISABLE_SECURITY exists for. Here we
        simulate that seeded admin role via the mock.
        """
        from app.database.models import Queue
        from app.database.enums import RoleName

        mock_db = AsyncMock()

        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value

        mock_user = MagicMock()
        mock_user.roles = [admin_role]

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.patch("/api/v1/queues/1", json={"name": "Updated"})

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_debug_header_impersonates_non_admin(
        self, TestClientWithMocks, security_disabled
    ):
        """The X-Debug-User-Id header lets a dev impersonate a different identity
        while security is disabled, e.g. to exercise the non-admin code path
        without needing real credentials.
        """
        from app.database.models import Queue
        from app.config import DEV_USER_ID

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.roles = []

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.patch(
            "/api/v1/queues/1",
            json={"name": "Updated"},
            headers={"X-Debug-User-Id": str(DEV_USER_ID)},
        )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_enforces_auth(self, TestClientWithMocks, admin_user_token, security_enabled, authenticated_user_id):
        """Verify security enforcement when explicitly enabled."""
        from app.database.models import Queue

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999

        async def mock_get(model, **kwargs):
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {admin_user_token}"}
            )

        assert response.status_code == 403
