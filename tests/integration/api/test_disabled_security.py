"""
Integration tests for security configuration.

Tests verify that security decorators work correctly with the
get_security_enabled() configuration mechanism. Disabling security no longer
skips authorization entirely - it resolves a dev identity (DEV_ADMIN_USER_ID
by default, or whatever the X-Debug-User-Id header requests) and runs the
same role/ownership checks against it that a real request would go through.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSecurityConfiguration:
    """Test security decorator behavior with configuration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_by_default(
        self,
        test_client_with_mocks: Any,
        admin_user_token: Any,
        authenticated_user_id: Any,
    ) -> None:
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

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = test_client_with_mocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {admin_user_token}"},
            )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_still_enforces_roles_for_default_identity(
        self,
        test_client_with_mocks: Any,
        security_disabled: Any,
    ) -> None:
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

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = test_client_with_mocks(mock_db=mock_db)

        response = test_client.patch("/api/v1/queues/1", json={"name": "Updated"})

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_allows_admin_dev_identity(
        self,
        test_client_with_mocks: Any,
        security_disabled: Any,
    ) -> None:
        """The default dev identity (DEV_ADMIN_USER_ID) is admin-roled in a real
        seeded dev DB, so role-gated endpoints succeed with no auth header at all -
        the "just works" dev experience DISABLE_SECURITY exists for. Here we
        simulate that seeded admin role via the mock.
        """
        from app.database.enums import RoleName
        from app.database.models import Queue

        mock_db = AsyncMock()

        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value

        mock_user = MagicMock()
        mock_user.roles = [admin_role]

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = test_client_with_mocks(mock_db=mock_db)

        response = test_client.patch("/api/v1/queues/1", json={"name": "Updated"})

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_debug_header_impersonates_non_admin(
        self,
        test_client_with_mocks: Any,
        security_disabled: Any,
    ) -> None:
        """The X-Debug-User-Id header lets a dev impersonate a different identity
        while security is disabled, e.g. to exercise the non-admin code path
        without needing real credentials.
        """
        from app.config import DEV_USER_ID
        from app.database.models import Queue

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.roles = []

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = test_client_with_mocks(mock_db=mock_db)

        response = test_client.patch(
            "/api/v1/queues/1",
            json={"name": "Updated"},
            headers={"X-Debug-User-Id": str(DEV_USER_ID)},
        )

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_bearer_token_sets_dev_identity(
        self,
        test_client_with_mocks: Any,
        security_disabled: Any,
    ) -> None:
        """When security is disabled, a Bearer token's ``sub`` is honored as the
        dev identity (decoded without signature verification) so dev behaves like
        prod: the caller follows whoever the frontend logged in as. Here a
        non-admin token for user 12345678 reaches their own user record via the
        ``matching_user_id_override`` - which would 403 if the identity fell back
        to ``DEV_ADMIN_USER_ID`` (1) instead.
        """
        from app.database.models import User
        from app.security import generate_token

        mock_db = AsyncMock()

        non_admin_user = MagicMock()
        non_admin_user.roles = []

        target_user: dict[str, Any] = {"id": 12345678, "profile": None, "roles": []}

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == User and kwargs.get("_include", {}).get("roles"):
                return non_admin_user
            return target_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = test_client_with_mocks(mock_db=mock_db)

        response = test_client.get(
            "/api/v1/users/12345678",
            headers={"Authorization": f"Bearer {generate_token(12345678)}"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == 12345678

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_disabled_malformed_bearer_falls_back_to_admin(
        self,
        test_client_with_mocks: Any,
        security_disabled: Any,
    ) -> None:
        """A malformed/unsigned Bearer value is ignored and resolution falls
        through to ``DEV_ADMIN_USER_ID``, preserving the "just works" dev
        experience for unauthenticated-style requests.
        """
        from app.database.enums import RoleName
        from app.database.models import Queue

        mock_db = AsyncMock()

        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value

        mock_user = MagicMock()
        mock_user.roles = [admin_role]

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999
        mock_queue.name = "Test Queue"

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = test_client_with_mocks(mock_db=mock_db)

        response = test_client.patch(
            "/api/v1/queues/1",
            json={"name": "Updated"},
            headers={"Authorization": "Bearer not-a-jwt"},
        )

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_enabled_enforces_auth(
        self,
        test_client_with_mocks: Any,
        admin_user_token: Any,
        security_enabled: Any,
        authenticated_user_id: Any,
    ) -> None:
        """Verify security enforcement when explicitly enabled."""
        from app.database.models import Queue

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = 12345678
        mock_user.roles = []

        mock_queue = MagicMock()
        mock_queue.id = 1
        mock_queue.user_id = 99999999

        async def mock_get(model: Any, **kwargs: Any) -> Any:
            if model == Queue:
                return mock_queue
            return mock_user

        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = test_client_with_mocks(mock_db=mock_db)

        with authenticated_user_id(12345678):
            response = test_client.patch(
                "/api/v1/queues/1",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {admin_user_token}"},
            )

        assert response.status_code == 403
