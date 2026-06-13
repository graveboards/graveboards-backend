"""
Unit tests for security overrides.

Tests the authorization override functions for user ID matching and queue ownership.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.security.overrides import matching_user_id_override, queue_owner_override
from app.database.models import Queue, Request


class TestMatchingUserIdOverride:
    """Test matching_user_id_override authorization check."""

    @pytest.mark.asyncio
    async def test_matching_user_ids_returns_true(self):
        """Test that matching user IDs return True."""
        result = await matching_user_id_override(
            user=123,
            user_id=123
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_non_matching_user_ids_returns_false(self):
        """Test that non-matching user IDs return False."""
        result = await matching_user_id_override(
            user={"id": 123},
            user_id=456
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_authenticated_user_id_null_returns_false(self):
        """Test that null authenticated user ID returns False."""
        result = await matching_user_id_override(
            user=None,
            user_id=123
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_resource_user_id_null_returns_false(self):
        """Test that null resource user ID returns False."""
        result = await matching_user_id_override(
            user={"id": 123},
            user_id=None
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_both_user_ids_null_returns_false(self):
        """Test that both null user IDs return False."""
        result = await matching_user_id_override(
            user=None,
            user_id=None
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_custom_authenticated_lookup_path(self):
        """Test with custom authenticated user lookup path."""
        result = await matching_user_id_override(
            authenticated_user_id_lookup="auth.user.id",
            resource_user_id_lookup="target_user_id",
            auth={"user": {"id": 789}},
            target_user_id=789
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_custom_resource_lookup_path(self):
        """Test with custom resource user ID lookup path."""
        result = await matching_user_id_override(
            authenticated_user_id_lookup="user",
            resource_user_id_lookup="resource.owner.id",
            user=111,
            resource={"owner": {"id": 111}}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_nested_user_id_lookup(self):
        """Test that nested structures are compared as dicts."""
        result = await matching_user_id_override(
            user={"profile": {"user_id": 222}},
            user_id={"profile": {"user_id": 222}}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_different_types_returns_false(self):
        """Test that different types (int vs string) return False."""
        result = await matching_user_id_override(
            user=123,
            user_id="123"
        )
        assert result is False


class TestQueueOwnerOverride:
    """Test queue_owner_override authorization check."""

    @pytest.mark.asyncio
    async def test_direct_queue_ownership_returns_true(self):
        """Test that authenticated user owns the queue directly."""
        mock_db = AsyncMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 123
        mock_db.get = AsyncMock(return_value=mock_queue)

        result = await queue_owner_override(
            db=mock_db,
            user=123,
            queue_id=1
        )

        assert result is True
        mock_db.get.assert_called_once_with(Queue, id=1)

    @pytest.mark.asyncio
    async def test_direct_queue_non_ownership_returns_false(self):
        """Test that non-owner user returns False."""
        mock_db = AsyncMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 456
        mock_db.get = AsyncMock(return_value=mock_queue)

        result = await queue_owner_override(
            db=mock_db,
            user=123,
            queue_id=1
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_request_based_ownership_returns_true(self):
        """Test ownership resolved via Request -> Queue."""
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 123
        mock_request.queue = mock_queue
        mock_db.get = AsyncMock(return_value=mock_request)

        result = await queue_owner_override(
            db=mock_db,
            user=123,
            request_id=1,
            from_request=True
        )

        assert result is True
        mock_db.get.assert_called_once_with(
            Request,
            id=1,
            _include={"queue": True}
        )

    @pytest.mark.asyncio
    async def test_request_based_non_ownership_returns_false(self):
        """Test non-ownership via Request -> Queue."""
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 456
        mock_request.queue = mock_queue
        mock_db.get = AsyncMock(return_value=mock_request)

        result = await queue_owner_override(
            db=mock_db,
            user=123,
            request_id=1,
            from_request=True
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_custom_authenticated_user_lookup(self):
        """Test with custom authenticated user ID lookup path."""
        mock_db = AsyncMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 789
        mock_db.get = AsyncMock(return_value=mock_queue)

        result = await queue_owner_override(
            db=mock_db,
            authenticated_user_id_lookup="auth.user.id",
            auth={"user": {"id": 789}},
            queue_id=1
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_different_users_returns_false(self):
        """Test that different users return False."""
        mock_db = AsyncMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 999
        mock_db.get = AsyncMock(return_value=mock_queue)

        result = await queue_owner_override(
            db=mock_db,
            user=111,
            queue_id=1
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_null_authenticated_user_returns_false(self):
        """Test that null authenticated user returns False."""
        mock_db = AsyncMock()
        mock_queue = MagicMock()
        mock_queue.user_id = 123
        mock_db.get = AsyncMock(return_value=mock_queue)

        result = await queue_owner_override(
            db=mock_db,
            user=None,
            queue_id=1
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_null_queue_user_id_returns_false(self):
        """Test that null queue user_id returns False."""
        mock_db = AsyncMock()
        mock_queue = MagicMock()
        mock_queue.user_id = None
        mock_db.get = AsyncMock(return_value=mock_queue)

        result = await queue_owner_override(
            db=mock_db,
            user=123,
            queue_id=1
        )

        assert result is False
