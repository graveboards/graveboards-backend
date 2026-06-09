import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from functools import wraps

from app.redis.decorators import rate_limit
from app.exceptions import RateLimitExceededError


class TestRateLimitDecorator:
    """Test rate_limit decorator behavior."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock_client = MagicMock()
        mock_client.incr = AsyncMock(return_value=1)
        mock_client.expire = AsyncMock(return_value=True)
        return mock_client

    @pytest.fixture
    def mock_redis_with_count(self, mock_redis_client):
        """Create mock Redis client with configurable count."""
        def set_incr_count(count):
            mock_redis_client.incr = AsyncMock(return_value=count)
        
        set_incr_count(1)
        return mock_redis_client, set_incr_count

    async def test_rate_limit_allows_under_limit(self, mock_redis_client):
        """Test that requests under the limit are allowed."""

        @rate_limit(limit_per_window=5, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=1)
        mock_redis_client.expire = AsyncMock(return_value=True)

        result = await test_func(mock_redis_client)

        assert result == "success"
        mock_redis_client.incr.assert_called_once()

    async def test_rate_limit_blocks_over_limit(self, mock_redis_client):
        """Test that requests over the limit are blocked."""

        @rate_limit(limit_per_window=2, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=3)
        mock_redis_client.expire = AsyncMock(return_value=True)

        with pytest.raises(RateLimitExceededError):
            await test_func(mock_redis_client)

    async def test_rate_limit_increments_counter(self, mock_redis_client):
        """Test that counter is incremented on each call."""

        @rate_limit(limit_per_window=10, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=1)
        mock_redis_client.expire = AsyncMock(return_value=True)

        for i in range(5):
            await test_func(mock_redis_client)

        assert mock_redis_client.incr.call_count == 5

    async def test_rate_limit_sets_expiry_on_first_call(self, mock_redis_client):
        """Test that expiry is set on first request."""

        @rate_limit(limit_per_window=10, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=1)
        mock_redis_client.expire = AsyncMock(return_value=True)

        await test_func(mock_redis_client)

        mock_redis_client.expire.assert_called_once()

    async def test_rate_limit_doesnt_set_expiry_on_subsequent_calls(self, mock_redis_client):
        """Test that expiry is not set on subsequent calls."""

        @rate_limit(limit_per_window=10, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(side_effect=[1, 2, 3])
        mock_redis_client.expire = AsyncMock(return_value=True)

        await test_func(mock_redis_client)
        await test_func(mock_redis_client)
        await test_func(mock_redis_client)

        assert mock_redis_client.expire.call_count == 1

    async def test_rate_limit_with_object_containing_rc(self):
        """Test rate limit with object containing rc attribute."""

        class Service:
            def __init__(self):
                self.rc = MagicMock()

            @rate_limit(limit_per_window=5, auto_retry=False)
            async def test_method(self):
                return "success"

        service = Service()
        service.rc.incr = AsyncMock(return_value=1)
        service.rc.expire = AsyncMock(return_value=True)

        result = await service.test_method()

        assert result == "success"

    async def test_rate_limit_auto_retry_disabled(self, mock_redis_client):
        """Test auto_retry=False raises error immediately."""

        @rate_limit(limit_per_window=1, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=2)
        mock_redis_client.expire = AsyncMock(return_value=True)

        with pytest.raises(RateLimitExceededError):
            await test_func(mock_redis_client)

    async def test_rate_limit_auto_retry_enabled(self, mock_redis_client):
        """Test auto_retry=True waits and retries."""

        @rate_limit(limit_per_window=1, auto_retry=True)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=2)
        mock_redis_client.expire = AsyncMock(return_value=True)

        with patch('app.redis.decorators.asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = AsyncMock()
            
            with pytest.raises(RateLimitExceededError):
                await test_func(mock_redis_client)

    async def test_rate_limit_with_custom_limit(self, mock_redis_client):
        """Test rate limit with custom limit value."""

        @rate_limit(limit_per_window=100, auto_retry=False)
        async def test_func(self):
            return "success"

        mock_redis_client.incr = AsyncMock(return_value=50)
        mock_redis_client.expire = AsyncMock(return_value=True)

        result = await test_func(mock_redis_client)

        assert result == "success"

    async def test_rate_limit_rejects_non_async_function(self):
        """Test that non-async functions raise error."""

        with pytest.raises(ValueError):

            @rate_limit(limit_per_window=5)
            def sync_func():
                return "success"

    async def test_rate_limit_rejects_no_redis_client(self):
        """Test that calls without Redis client raise error."""

        @rate_limit(limit_per_window=5, auto_retry=False)
        async def test_func():
            return "success"

        with pytest.raises(ValueError):
            await test_func()

    async def test_rate_limit_rejects_invalid_first_arg(self):
        """Test that invalid first argument raises error."""

        @rate_limit(limit_per_window=5, auto_retry=False)
        async def test_func(invalid_arg):
            return "success"

        with pytest.raises(ValueError):
            await test_func("not_a_redis_client")

    async def test_rate_limit_wraps_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @rate_limit(limit_per_window=5, auto_retry=False)
        async def my_test_function(self):
            """My test docstring."""
            return "success"

        assert my_test_function.__name__ == "my_test_function"
        assert my_test_function.__doc__ == "My test docstring."

    async def test_rate_limit_different_limits_independent(self):
        """Test that different functions have independent limits."""

        @rate_limit(limit_per_window=2, auto_retry=False)
        async def func_a(self):
            return "a"

        @rate_limit(limit_per_window=3, auto_retry=False)
        async def func_b(self):
            return "b"

        mock_client_a = MagicMock()
        mock_client_a.incr = AsyncMock(side_effect=[1, 2, 3])
        mock_client_a.expire = AsyncMock(return_value=True)

        mock_client_b = MagicMock()
        mock_client_b.incr = AsyncMock(side_effect=[1, 2, 3, 4])
        mock_client_b.expire = AsyncMock(return_value=True)

        await func_a(mock_client_a)
        await func_a(mock_client_a)

        with pytest.raises(RateLimitExceededError):
            await func_a(mock_client_a)

        await func_b(mock_client_b)
        await func_b(mock_client_b)
        await func_b(mock_client_b)

        with pytest.raises(RateLimitExceededError):
            await func_b(mock_client_b)
