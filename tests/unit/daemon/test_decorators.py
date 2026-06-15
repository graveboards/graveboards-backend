import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from app.daemon.services.decorators import auto_retry, MAX_ATTEMPTS


class TestAutoRetryDecorator:
    """Test auto_retry decorator."""

    async def test_auto_retry_succeeds_on_first_attempt(self):
        """Test successful function on first attempt."""
        call_count = 0

        @auto_retry(max_attempts=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()

        assert result == "success"
        assert call_count == 1

    async def test_auto_retry_retries_on_failure(self):
        """Test automatic retry on exception."""
        call_count = 0

        @auto_retry(max_attempts=3, retry_exceptions=(ValueError,))
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await failing_func()

        assert result == "success"
        assert call_count == 3

    async def test_auto_retry_raises_after_max_attempts(self):
        """Test that exception is raised after max attempts."""
        call_count = 0

        @auto_retry(max_attempts=3, retry_exceptions=(ValueError,))
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            await always_fails()

        assert call_count == 3

    async def test_auto_retry_uses_default_max_attempts(self):
        """Test that default max_attempts is used."""
        call_count = 0

        @auto_retry()
        async def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < MAX_ATTEMPTS:
                raise TimeoutError()
            return "success"

        result = await fails_twice()

        assert result == "success"
        assert call_count == MAX_ATTEMPTS

    async def test_auto_retry_respects_exception_types(self):
        """Test that only specified exceptions trigger retry."""
        call_count = 0

        @auto_retry(max_attempts=3, retry_exceptions=(TimeoutError,))
        async def raises_different_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Wrong exception type")

        with pytest.raises(ValueError):
            await raises_different_error()

        assert call_count == 1

    async def test_auto_retry_logs_retry_attempts(self):
        """Test that retry attempts are logged."""
        call_count = 0

        @auto_retry(max_attempts=3, retry_exceptions=(ValueError,))
        async def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError()
            return "success"

        with patch("app.daemon.services.decorators.logger") as mock_logger:
            await fails_twice()

        assert mock_logger.warning.called
        mock_logger.warning.assert_called()

    async def test_auto_retry_logs_final_failure(self):
        """Test that final failure is logged."""
        @auto_retry(max_attempts=2, retry_exceptions=(ValueError,))
        async def always_fails():
            raise ValueError()

        with patch("app.daemon.services.decorators.logger") as mock_logger:
            with pytest.raises(ValueError):
                await always_fails()

        assert mock_logger.error.called

    async def test_auto_retry_catches_asyncio_timeout(self):
        """Test that asyncio.TimeoutError can be caught."""
        call_count = 0

        @auto_retry(max_attempts=3, retry_exceptions=(asyncio.TimeoutError,))
        async def timeout_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError()
            return "success"

        result = await timeout_then_succeed()

        assert result == "success"
        assert call_count == 3

    async def test_auto_retry_does_not_retry_non_async_functions(self):
        """Test that non-async functions raise ValueError."""
        with pytest.raises(ValueError, match="must be async"):

            @auto_retry()
            def sync_func():
                return "sync"

    async def test_auto_retry_preserves_function_name(self):
        """Test that function name is preserved."""
        @auto_retry()
        async def my_custom_function():
            return "result"

        assert my_custom_function.__name__ == "my_custom_function"

    async def test_auto_retry_with_zero_delay_backoff(self):
        """Test that zero delay backoff works."""
        call_count = 0

        @auto_retry(
            max_attempts=3,
            retry_exceptions=(ValueError,),
            backoff_strategy=lambda n: 0
        )
        async def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError()
            return "success"

        result = await fails_twice()

        assert result == "success"
        assert call_count == 3

    async def test_auto_retry_with_custom_exception_tuple(self):
        """Test with custom exception types tuple."""
        call_count = 0

        @auto_retry(
            max_attempts=3,
            retry_exceptions=(ValueError, TypeError)
        )
        async def raises_type_error():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TypeError()
            return "success"

        result = await raises_type_error()

        assert result == "success"
        assert call_count == 3

    async def test_auto_retry_does_not_retry_unspecified_exceptions(self):
        """Test that unspecified exceptions are not retried."""
        call_count = 0

        @auto_retry(
            max_attempts=5,
            retry_exceptions=(TimeoutError,)
        )
        async def raises_key_error():
            nonlocal call_count
            call_count += 1
            raise KeyError()

        with pytest.raises(KeyError):
            await raises_key_error()

        assert call_count == 1
