
from app.redis.enums import Namespace


class TestNamespaceKeys:
    """Test Redis namespace key generation."""

    def test_namespace_has_hash_name_method(self):
        """Test that namespace has hash_name method."""
        assert hasattr(Namespace, "hash_name")
        assert callable(Namespace.hash_name)

    def test_lock_namespace(self):
        """Test lock namespace key generation."""
        result = Namespace.LOCK.hash_name("123")
        assert result == "lock:123"

    def test_rate_limit_counter_namespace(self):
        """Test rate limit counter namespace key generation."""
        result = Namespace.RATE_LIMIT_COUNTER.hash_name(1234567890)
        assert result == "rate_limit_counter:1234567890"

    def test_osu_client_oauth_token_namespace(self):
        """Test OAuth token namespace key generation."""
        result = Namespace.OSU_CLIENT_OAUTH_TOKEN.hash_name("user123")
        assert result == "osu_client_oauth_token:user123"

    def test_osu_user_profile_namespace(self):
        """Test user profile namespace key generation."""
        result = Namespace.OSU_USER_PROFILE.hash_name(456)
        assert result == "osu_user_profile:456"

    def test_csrf_state_namespace(self):
        """Test CSRF state namespace key generation."""
        result = Namespace.CSRF_STATE.hash_name("random_state")
        assert result == "csrf_state:random_state"

    def test_queue_request_handler_task_namespace(self):
        """Test queue request handler namespace key generation."""
        result = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(789)
        assert result == "queue_request_handler_task:789"

    def test_cached_beatmap_namespace(self):
        """Test cached beatmap namespace key generation."""
        result = Namespace.CACHED_BEATMAP.hash_name(999)
        assert result == "cached_beatmap:999"

    def test_cached_beatmapset_namespace(self):
        """Test cached beatmapset namespace key generation."""
        result = Namespace.CACHED_BEATMAPSET.hash_name(111)
        assert result == "cached_beatmapset:111"

    def test_hash_name_with_string_suffix(self):
        """Test hash_name with string suffix."""
        result = Namespace.LOCK.hash_name("string_suffix")
        assert result == "lock:string_suffix"

    def test_hash_name_with_integer_suffix(self):
        """Test hash_name with integer suffix."""
        result = Namespace.LOCK.hash_name(999999)
        assert result == "lock:999999"

    def test_different_namespaces_different_prefixes(self):
        """Test that different namespaces have different prefixes."""
        lock_key = Namespace.LOCK.hash_name("test")
        rate_key = Namespace.RATE_LIMIT_COUNTER.hash_name("test")

        assert lock_key != rate_key
        assert lock_key.startswith("lock:")
        assert rate_key.startswith("rate_limit_counter:")

    def test_hash_name_deterministic(self):
        """Test that hash_name is deterministic."""
        result1 = Namespace.LOCK.hash_name("test")
        result2 = Namespace.LOCK.hash_name("test")

        assert result1 == result2

    def test_namespace_values(self):
        """Test namespace enum values."""
        assert Namespace.LOCK == "lock"
        assert Namespace.RATE_LIMIT_COUNTER == "rate_limit_counter"
        assert Namespace.OSU_CLIENT_OAUTH_TOKEN == "osu_client_oauth_token"
        assert Namespace.OSU_USER_PROFILE == "osu_user_profile"
        assert Namespace.CSRF_STATE == "csrf_state"
        assert Namespace.QUEUE_REQUEST_HANDLER_TASK == "queue_request_handler_task"
        assert Namespace.CACHED_BEATMAP == "cached_beatmap"
        assert Namespace.CACHED_BEATMAPSET == "cached_beatmapset"

    def test_hash_name_with_special_characters(self):
        """Test hash_name with special characters in suffix."""
        result = Namespace.LOCK.hash_name("user-123_test")
        assert result == "lock:user-123_test"

    def test_hash_name_empty_suffix(self):
        """Test hash_name with empty suffix."""
        result = Namespace.LOCK.hash_name("")
        assert result == "lock:"

    def test_all_namespaces_covered(self):
        """Test that all namespace enum values work with hash_name."""
        namespaces = [
            Namespace.LOCK,
            Namespace.RATE_LIMIT_COUNTER,
            Namespace.OSU_CLIENT_OAUTH_TOKEN,
            Namespace.OSU_USER_PROFILE,
            Namespace.CSRF_STATE,
            Namespace.QUEUE_REQUEST_HANDLER_TASK,
            Namespace.CACHED_BEATMAP,
            Namespace.CACHED_BEATMAPSET,
        ]

        for ns in namespaces:
            result = ns.hash_name("test")
            assert isinstance(result, str)
            assert result.startswith(f"{ns}:")
