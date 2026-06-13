"""
Unit tests for security decorators.

Tests the decorator logic and configuration behavior without full HTTP stack.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.security.decorators import role_authorization, ownership_authorization
from app.database.enums import RoleName
from app.config import DISABLE_SECURITY


class TestRoleAuthorizationConfiguration:
    """Test role_authorization decorator behavior with different configurations."""

    @pytest.mark.asyncio
    async def test_decorator_marked_with_security_flag(self):
        """Test that decorator is properly marked for security introspection."""
        @role_authorization(RoleName.ADMIN)
        async def admin_endpoint(**kwargs):
            return {"data": "success"}
        
        assert hasattr(admin_endpoint, '__security_authorization__')
        assert admin_endpoint.__security_authorization__ is True

    @pytest.mark.asyncio
    async def test_non_async_function_raises_error(self):
        """Test that non-async functions raise ValueError."""
        with pytest.raises(ValueError, match="must be async"):
            @role_authorization(RoleName.ADMIN)
            def sync_endpoint(**kwargs):
                return {"data": "success"}

    @pytest.mark.asyncio
    async def test_mutually_exclusive_args_raises_error(self):
        """Test that required_roles and one_of together raise ValueError."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            @role_authorization(RoleName.ADMIN, one_of=[RoleName.ADMIN])
            async def endpoint(**kwargs):
                return {"data": "success"}

    @pytest.mark.asyncio
    async def test_missing_both_args_raises_error(self):
        """Test that missing both required_roles and one_of raises ValueError."""
        with pytest.raises(ValueError, match="Must provide either"):
            @role_authorization()
            async def endpoint(**kwargs):
                return {"data": "success"}


class TestOwnershipAuthorizationConfiguration:
    """Test ownership_authorization decorator behavior."""

    @pytest.mark.asyncio
    async def test_decorator_marked_with_security_flag(self):
        """Test that decorator is properly marked for security introspection."""
        @ownership_authorization()
        async def endpoint(**kwargs):
            return ({"data": "success"}, 200)
        
        assert hasattr(endpoint, '__security_authorization__')
        assert endpoint.__security_authorization__ is True

    @pytest.mark.asyncio
    async def test_non_async_function_raises_error(self):
        """Test that non-async functions raise ValueError."""
        with pytest.raises(ValueError, match="must be async"):
            @ownership_authorization()
            def sync_endpoint(**kwargs):
                return ({"data": "success"}, 200)


class TestSecurityConfigBehavior:
    """Test decorator behavior with DISABLE_SECURITY configuration."""

    @pytest.mark.asyncio
    async def test_disable_security_true_allows_anyone(self):
        """Test that DISABLE_SECURITY=True bypasses all checks."""
        with patch('app.security.decorators.DISABLE_SECURITY', True):
            @role_authorization(RoleName.ADMIN)
            async def endpoint(**kwargs):
                return {"data": "success"}
            
            mock_db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = 123
            mock_user.roles = []
            mock_db.get = AsyncMock(return_value=mock_user)
            
            scope = {"state": {}}
            scope["state"]["db"] = mock_db
            
            kwargs = {"token_info": {"sub": 999}}
            
            result = await endpoint(**kwargs)
            
            assert result == {"data": "success"}
            mock_db.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_disable_security_false_enforces_auth(self):
        """Test that DISABLE_SECURITY=False enforces authorization."""
        with patch('app.security.decorators.DISABLE_SECURITY', False):
            @role_authorization(RoleName.ADMIN)
            async def endpoint(**kwargs):
                return {"data": "success"}
            
            mock_db = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = 456
            mock_user.roles = []
            mock_db.get = AsyncMock(return_value=mock_user)
            
            scope = {"state": {}}
            scope["state"]["db"] = mock_db
            
            kwargs = {"token_info": {"sub": 456}}
            
            with pytest.raises(Exception):
                await endpoint(**kwargs)
