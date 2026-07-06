"""Unit tests for Redis distributed lock (lock_ctx)."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.redis.rc import RedisClient
from app.exceptions import RedisLockTimeoutError


class TestLockCtx:
    """Test distributed lock acquisition and release."""

    @pytest.fixture
    def mock_rc(self):
        """Create a mock RedisClient with configurable set/eval behavior."""
        rc = MagicMock(spec=RedisClient)
        rc.set = AsyncMock()
        rc.eval = AsyncMock(return_value=1)
        return rc

    @pytest.mark.asyncio
    async def test_lock_acquired_on_first_set(self, mock_rc):
        """Test lock acquires successfully when SET NX returns True."""
        mock_rc.set.return_value = True

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", timeout=0.1):
            mock_rc.set.assert_called_once()
            call_kwargs = mock_rc.set.call_args
            assert call_kwargs[1]["nx"] is True
            assert call_kwargs[1]["ex"] == 10

    @pytest.mark.asyncio
    async def test_lock_released_with_lua_script(self, mock_rc):
        """Test lock release uses atomic Lua script (GET + DEL conditional)."""
        mock_rc.set.return_value = True

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", timeout=0.1):
            pass

        mock_rc.eval.assert_called_once()
        lua_script = mock_rc.eval.call_args[0][0]
        assert 'redis.call("get"' in lua_script
        assert 'redis.call("del"' in lua_script

    @pytest.mark.asyncio
    async def test_lock_releases_only_if_token_matches(self, mock_rc):
        """Test Lua script only deletes the key if the token still matches."""
        mock_rc.set.return_value = True
        mock_rc.eval.return_value = 0

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", timeout=0.1):
            pass

        mock_rc.eval.assert_called_once()
        call_args = mock_rc.eval.call_args
        assert call_args[0][1] == 1  # KEYS[1]
        assert call_args[0][2] == "test_lock"

    @pytest.mark.asyncio
    async def test_lock_retries_until_acquired(self, mock_rc):
        """Test lock retries SET NX until it succeeds."""
        mock_rc.set.side_effect = [None, None, True]

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", timeout=5.0):
            pass

        assert mock_rc.set.call_count == 3

    @pytest.mark.asyncio
    async def test_lock_timeout_raises_error(self, mock_rc):
        """Test lock timeout raises RedisLockTimeoutError when key never available."""
        mock_rc.set.return_value = None

        with pytest.raises(RedisLockTimeoutError) as exc_info:
            async with RedisClient.lock_ctx(mock_rc, key="stuck_lock", timeout=0.01):
                pass

        assert exc_info.value.key == "stuck_lock"

    @pytest.mark.asyncio
    async def test_lock_generates_random_token(self, mock_rc):
        """Test lock generates a unique random token passed to SET."""
        mock_rc.set.return_value = True

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", timeout=0.1):
            pass

        call_args = mock_rc.set.call_args
        token = call_args[1]["value"] if "value" in call_args[1] else call_args[0][1]
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_lock_passes_expiry_to_set(self, mock_rc):
        """Test lock passes the configured expiry to SET."""
        mock_rc.set.return_value = True

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", expiry=30):
            pass

        call_kwargs = mock_rc.set.call_args[1]
        assert call_kwargs["ex"] == 30

    @pytest.mark.asyncio
    async def test_lock_yields_control_to_context(self, mock_rc):
        """Test that code inside the lock context executes."""
        mock_rc.set.return_value = True
        executed = []

        async with RedisClient.lock_ctx(mock_rc, key="test_lock", timeout=0.1):
            executed.append("inside")

        assert executed == ["inside"]
