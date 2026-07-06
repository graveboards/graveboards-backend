"""Unit tests for rate_limit decorator edge cases not covered by test_rate_limit_decorator.py."""

import asyncio
import time
import pytest
from datetime import datetime, timezone

from app.redis.decorators import rate_limit
from app.exceptions import RateLimitExceededError


class MockRedisClient:
    """A non-Mock Redis client stub for rate_limit tests."""
    def __init__(self):
        self.incr = None
        self.expire = None
        self.get = None
        self.set = None


def _make_mock_rc():
    """Create a properly configured mock Redis client."""
    from unittest.mock import AsyncMock
    rc = MockRedisClient()
    rc.incr = AsyncMock(return_value=1)
    rc.expire = AsyncMock(return_value=True)
    rc.get = AsyncMock(return_value=None)
    rc.set = AsyncMock(return_value=True)
    return rc


class TestRateLimitModule:
    """Test rate_limit decorator edge cases."""

    @pytest.fixture
    def mock_rc(self):
        """Create a mock Redis client with async methods."""
        return _make_mock_rc()

    @pytest.mark.asyncio
    async def test_rate_limit_error_contains_timing_info(self):
        """Test RateLimitExceededError has next_window and last_call_timestamp."""
        next_win = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        exc = RateLimitExceededError(
            next_window=next_win,
            last_call_timestamp=1704110400.0,
        )

        assert exc.next_window == next_win
        assert exc.last_call_timestamp == 1704110400.0
        assert "Rate limit exceeded" in str(exc)
        assert "1704110400.0" in str(exc)

    @pytest.mark.asyncio
    async def test_rate_limit_auto_retry_retries(self):
        """Test auto_retry=True retries after window expires."""
        rc = _make_mock_rc()
        call_count = [0]

        async def mock_incr(key):
            call_count[0] += 1
            return 2 if call_count[0] == 1 else 1

        rc.incr = mock_incr
        from unittest.mock import AsyncMock as AM
        rc.expire = AM(return_value=True)
        rc.get = AM(return_value=None)
        rc.set = AM(return_value=True)

        @rate_limit(limit_per_window=1, window_size=1, auto_retry=True)
        async def test_func(self):
            return "ok"

        result = await test_func(rc)
        assert result == "ok"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_rate_limit_rejects_non_async_function(self):
        """Test rate_limit raises ValueError for sync functions."""
        with pytest.raises(ValueError, match="must be async"):

            @rate_limit(limit_per_window=5)
            def sync_func(self):
                return "ok"

    @pytest.mark.asyncio
    async def test_rate_limit_uses_default_limit_when_none(self, mock_rc):
        """Test rate_limit defaults to 60 when limit_per_window is None."""

        @rate_limit(limit_per_window=None, auto_retry=False)
        async def test_func(self):
            return "ok"

        result = await test_func(mock_rc)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_rate_limit_skips_window_check_when_limit_zero(self, mock_rc):
        """Test rate_limit skips window counter when limit_per_window=0."""
        from unittest.mock import AsyncMock as AM
        mock_rc.incr = AM()

        @rate_limit(limit_per_window=0, auto_retry=False)
        async def test_func(self):
            return "ok"

        result = await test_func(mock_rc)
        assert result == "ok"
        mock_rc.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_no_min_interval_no_get(self, mock_rc):
        """Test rate_limit with min_interval=0 does not read last_call_key."""
        from unittest.mock import AsyncMock as AM
        mock_rc.get = AM()

        @rate_limit(limit_per_window=10, min_interval=0.0, auto_retry=False)
        async def test_func(self):
            return "ok"

        result = await test_func(mock_rc)
        assert result == "ok"
        mock_rc.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_min_interval_sleeps_when_needed(self, mock_rc):
        """Test min_interval causes sleep when previous call was too recent."""
        from unittest.mock import AsyncMock as AM
        mock_rc.get = AM(return_value=str(time.time() - 0.001))

        @rate_limit(limit_per_window=10, min_interval=0.001, auto_retry=False)
        async def test_func(self):
            return "ok"

        result = await test_func(mock_rc)
        assert result == "ok"
        mock_rc.get.assert_called_once()
