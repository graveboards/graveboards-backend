"""Tests for conftest fixtures: security_disabled, security_enabled, admin_user_token."""

import pytest


class TestConftestFixtures:
    """Test conftest fixture behavior."""

    def test_security_disabled_fixture(self, security_disabled):
        """Test security_disabled temporarily disables security."""
        from app.config import get_security_enabled
        assert get_security_enabled() is False

    def test_security_enabled_fixture(self, security_enabled):
        """Test security_enabled temporarily enables security."""
        from app.config import get_security_enabled
        assert get_security_enabled() is True

    def test_admin_user_token_returns_string(self, admin_user_token):
        """Test admin_user_token generates a non-empty string."""
        assert isinstance(admin_user_token, str)
        assert len(admin_user_token) > 0

    def test_admin_user_token_starts_with_bearer(self, admin_user_token):
        """Test admin_user_token is a JWT (starts with eyJ)."""
        assert admin_user_token.startswith("eyJ")

    def test_security_disabled_restores_after(self):
        """Test security_disabled restores original state after context."""
        from app.config import get_security_enabled, override_security_enabled

        original = get_security_enabled()
        with override_security_enabled(False):
            assert get_security_enabled() is False
        assert get_security_enabled() == original

    def test_security_enabled_restores_after(self):
        """Test security_enabled restores original state after context."""
        from app.config import get_security_enabled, override_security_enabled

        original = get_security_enabled()
        with override_security_enabled(True):
            assert get_security_enabled() is True
        assert get_security_enabled() == original
