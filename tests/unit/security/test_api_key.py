import pytest
from unittest.mock import MagicMock, patch

from app.security.api_key import (
    generate_api_key,
    hash_api_key,
    validate_api_key,
)


class TestApiKey:
    """Test API key hashing and validation."""

    def test_generate_api_key_returns_string(self):
        """Test that generate_api_key returns a string."""
        result = generate_api_key()

        assert isinstance(result, str)

    def test_generate_api_key_has_expected_length(self):
        """Test that generate_api_key returns key of expected length."""
        result = generate_api_key()

        assert len(result) == 64  # API_KEY_LENGTH

    def test_generate_api_key_uses_secure_random(self):
        """Test that generate_api_key uses secure random generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert key1 != key2

    def test_generate_api_key_uses_alphanumeric_chars(self):
        """Test that generate_api_key uses alphanumeric characters."""
        result = generate_api_key()

        assert result.isalnum()

    def test_hash_api_key_returns_sha256_hex(self):
        """Test that hash_api_key returns SHA-256 hex digest."""
        result = hash_api_key("test_key")

        assert len(result) == 64  # SHA-256 produces 64 hex chars
        assert result == "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

    def test_hash_api_key_is_deterministic(self):
        """Test that hash_api_key is deterministic."""
        key = "test_key"

        result1 = hash_api_key(key)
        result2 = hash_api_key(key)

        assert result1 == result2

    def test_hash_api_key_different_keys_different_hashes(self):
        """Test that different keys produce different hashes."""
        key1 = "key1"
        key2 = "key2"

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2

    def test_hash_api_key_empty_string(self):
        """Test hashing of empty string."""
        result = hash_api_key("")

        assert len(result) == 64

    def test_hash_api_key_special_characters(self):
        """Test hashing of special characters."""
        result = hash_api_key("key@#$%^&*()")

        assert len(result) == 64

    def test_validate_api_key_valid(self):
        """Test validation of valid API key."""
        from app.database.models.api_key import ApiKey
        from datetime import datetime, timedelta
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

    def test_validate_api_key_not_found(self):
        """Test validation of missing API key."""
        with pytest.raises(ValueError, match="API key not found"):
            validate_api_key(None)

    def test_validate_api_key_expired(self):
        """Test validation of expired API key."""
        from app.database.models.api_key import ApiKey
        from datetime import datetime, timedelta
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() - timedelta(hours=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with pytest.raises(ValueError, match="API key has expired"):
            validate_api_key(api_key)

    def test_validate_api_key_revoked(self):
        """Test validation of revoked API key."""
        from app.database.models.api_key import ApiKey
        from datetime import datetime, timedelta
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() + timedelta(hours=1)
        api_key.is_revoked = True
        api_key.user_id = 123
        api_key.created_at = aware_utcnow()

        with pytest.raises(ValueError, match="API key is revoked"):
            validate_api_key(api_key)

    def test_validate_api_key_payload_structure(self):
        """Test that validate_api_key returns correct payload structure."""
        from app.database.models.api_key import ApiKey
        from datetime import datetime, timedelta
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

    def test_validate_api_key_timestamps_are_integers(self):
        """Test that validate_api_key returns integer timestamps."""
        from app.database.models.api_key import ApiKey
        from datetime import datetime, timedelta
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

    def test_validate_api_key_exp_after_iat(self):
        """Test that exp is after iat in payload."""
        from app.database.models.api_key import ApiKey
        from datetime import datetime, timedelta
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

    def test_generate_multiple_keys_unique(self):
        """Test that multiple generated keys are unique."""
        keys = [generate_api_key() for _ in range(10)]

        assert len(set(keys)) == 10

    def test_hash_api_key_long_key(self):
        """Test hashing of long API key."""
        long_key = "a" * 1000
        result = hash_api_key(long_key)

        assert len(result) == 64

    def test_validate_api_key_current_time_not_expired(self):
        """Test that key is not expired when current time is before expires_at."""
        from app.database.models.api_key import ApiKey
        from datetime import timedelta
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

    def test_validate_api_key_current_time_expired(self):
        """Test that key is expired when current time is at or after expires_at."""
        from app.database.models.api_key import ApiKey
        from datetime import timedelta
        from app.utils import aware_utcnow

        api_key = MagicMock(spec=ApiKey)
        api_key.expires_at = aware_utcnow() - timedelta(seconds=1)
        api_key.is_revoked = False
        api_key.user_id = 123
        api_key.created_at = aware_utcnow() - timedelta(hours=1)

        with pytest.raises(ValueError, match="API key has expired"):
            validate_api_key(api_key)

    def test_validate_api_key_with_just_expiring_key(self):
        """Test validation of key that expires now."""
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
