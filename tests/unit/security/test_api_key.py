from unittest.mock import MagicMock, patch

import pytest

from app.security.api_key import (
    generate_api_key,
    hash_api_key,
    validate_api_key,
)


class TestApiKey:
    """Test API key hashing and validation."""

    def test_generate_api_key_returns_string(self) -> None:
        """Test that generate_api_key returns a string."""
        result = generate_api_key()

        assert isinstance(result, str)

    def test_generate_api_key_has_expected_length(self) -> None:
        """Test that generate_api_key returns key of expected length."""
        result = generate_api_key()

        assert len(result) == 32  # API_KEY_LENGTH

    def test_generate_api_key_uses_secure_random(self) -> None:
        """Test that generate_api_key uses secure random generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert key1 != key2

    def test_generate_api_key_uses_alphanumeric_chars(self) -> None:
        """Test that generate_api_key uses alphanumeric characters."""
        result = generate_api_key()

        assert result.isalnum()

    def test_hash_api_key_returns_sha256_hex(self) -> None:
        """Test that hash_api_key returns SHA-256 hex digest."""
        result = hash_api_key("test_key")

        assert len(result) == 64  # SHA-256 produces 64 hex chars

    def test_hash_api_key_is_deterministic(self) -> None:
        """Test that hash_api_key is deterministic."""
        key = "test_key"

        result1 = hash_api_key(key)
        result2 = hash_api_key(key)

        assert result1 == result2

    def test_hash_api_key_different_keys_different_hashes(self) -> None:
        """Test that different keys produce different hashes."""
        key1 = "key1"
        key2 = "key2"

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2

    def test_hash_api_key_empty_string(self) -> None:
        """Test hashing of empty string."""
        result = hash_api_key("")

        assert len(result) == 64

    def test_hash_api_key_special_characters(self) -> None:
        """Test hashing of special characters."""
        result = hash_api_key("key@#$%^&*()")

        assert len(result) == 64

    def test_validate_api_key_valid(self) -> None:
        """Test validation of valid API key."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with patch("app.security.api_key.aware_utcnow") as mock_now:
            mock_now.return_value = aware_utcnow() - timedelta(hours=1)
            result = validate_api_key(api_key)

        assert result["sub"] == 123
        assert "iat" in result
        assert "exp" in result

    def test_validate_api_key_not_found(self) -> None:
        """Test validation of missing API key."""
        with pytest.raises(ValueError, match="API key not found"):
            validate_api_key(None)

    def test_validate_api_key_expired(self) -> None:
        """Test validation of expired API key."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() - timedelta(hours=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with pytest.raises(ValueError, match="API key has expired"):
            validate_api_key(api_key)

    def test_validate_api_key_revoked(self) -> None:
        """Test validation of revoked API key."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=1)
        api_key.is_revoked = True
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with pytest.raises(ValueError, match="API key is revoked"):
            validate_api_key(api_key)

    def test_validate_api_key_payload_structure(self) -> None:
        """Test that validate_api_key returns correct payload structure."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with patch("app.security.api_key.aware_utcnow") as mock_now:
            mock_now.return_value = aware_utcnow() - timedelta(hours=1)
            result = validate_api_key(api_key)

        assert "sub" in result
        assert "iat" in result
        assert "exp" in result
        assert result["sub"] == 123
        assert isinstance(result["iat"], int)
        assert isinstance(result["exp"], int)

    def test_validate_api_key_timestamps_are_integers(self) -> None:
        """Test that validate_api_key returns integer timestamps."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with patch("app.security.api_key.aware_utcnow") as mock_now:
            mock_now.return_value = aware_utcnow() - timedelta(hours=1)
            result = validate_api_key(api_key)

        assert isinstance(result["iat"], int)
        assert isinstance(result["exp"], int)

    def test_validate_api_key_exp_after_iat(self) -> None:
        """Test that exp is after iat in payload."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=2)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow() + timedelta(hours=1)

        with patch("app.security.api_key.aware_utcnow") as mock_now:
            mock_now.return_value = aware_utcnow()
            result = validate_api_key(api_key)

        assert result["exp"] > result["iat"]

    def test_generate_multiple_keys_unique(self) -> None:
        """Test that multiple generated keys are unique."""
        keys = [generate_api_key() for _ in range(10)]

        assert len(set(keys)) == 10

    def test_hash_api_key_long_key(self) -> None:
        """Test hashing of long API key."""
        long_key = "a" * 1000
        result = hash_api_key(long_key)

        assert len(result) == 64

    def test_validate_api_key_current_time_not_expired(self) -> None:
        """Test that key is not expired when current time is before expires_at."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with patch("app.security.api_key.aware_utcnow") as mock_now:
            mock_now.return_value = aware_utcnow()
            result = validate_api_key(api_key)

        assert result is not None

    def test_validate_api_key_current_time_expired(self) -> None:
        """Test that key is expired when current time is at or after expires_at."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() - timedelta(seconds=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow() - timedelta(hours=1)

        with pytest.raises(ValueError, match="API key has expired"):
            validate_api_key(api_key)

    def test_validate_api_key_with_just_expiring_key(self) -> None:
        """Test validation of key that expires now."""
        from datetime import timedelta

        from app.database.models.api_key import ApiKey
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow()
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow() - timedelta(hours=1)

        # Key that expires now should be considered expired
        with pytest.raises(ValueError, match="API key has expired"):
            validate_api_key(api_key)
