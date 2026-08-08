from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.osu_api.client.osu_api_client import OsuAPIClient
from tests._helpers.mocks import MockLockCtx


@pytest.fixture(autouse=True)
def mock_rate_limit_decorator() -> Generator[None]:
    with patch(
        "app.osu_api.client.osu_api_client.rate_limit", lambda *args, **kwargs: lambda func: func
    ):
        yield


@pytest.fixture
def api_client() -> Generator[tuple[OsuAPIClient, MagicMock]]:
    from app.oauth import OAuth

    mock_redis = AsyncMock()

    # Use a mock that can be easily overridden by tests
    mock_redis.hgetall = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)
    mock_redis.incr = AsyncMock(return_value=1)

    mock_redis.lock_ctx = MagicMock(return_value=MockLockCtx())

    # Create a mock httpx client
    mock_http_client = MagicMock()
    mock_http_client.get = AsyncMock()
    mock_http_client.post = AsyncMock()

    # Patch httpx.AsyncClient to return our mock before creating OsuAPIClient
    with patch("httpx.AsyncClient", return_value=mock_http_client):
        client = OsuAPIClient(mock_redis)

        # Patch OAuth's fetch_token to avoid real API calls
        async def mock_fetch_token(*args: Any, **kwargs: Any) -> dict[str, Any]:
            import time

            return {
                "access_token": "test-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": int(time.time()) + 3600,
            }

        with patch.object(OAuth, "fetch_token", mock_fetch_token):
            yield client, mock_redis


class MockResponse:
    def __init__(self, data: Any, status_code: int = 200) -> None:
        self._data = data
        self._status_code = status_code

    def json(self) -> Any:
        return self._data

    def raise_for_status(self) -> None:
        if self._status_code >= 400:
            raise Exception(f"HTTP {self._status_code}")
