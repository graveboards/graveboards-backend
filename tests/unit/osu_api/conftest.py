import pytest
from unittest.mock import AsyncMock, MagicMock, patch




@pytest.fixture(autouse=True)
def mock_rate_limit_decorator():
    with patch('app.osu_api.client.osu_api_client.rate_limit', lambda *args, **kwargs: lambda func: func):
        yield


@pytest.fixture
def api_client():
    from app.osu_api.client.osu_api_client import OsuAPIClient
    from app.oauth import OAuth

    mock_redis = MagicMock()
    
    # Use a mock that can be easily overridden by tests
    mock_redis.hgetall = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.lock_ctx = MagicMock()
    mock_redis.lock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_redis.lock_ctx.__aexit__ = AsyncMock(return_value=None)

    client = OsuAPIClient(mock_redis)
    
    # Patch OAuth's fetch_token to avoid real API calls
    async def mock_fetch_token(*args, **kwargs):
        import time
        return {
            "access_token": "test-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": int(time.time()) + 3600,
        }
    
    with patch.object(OAuth, 'fetch_token', mock_fetch_token):
        yield client, mock_redis


class MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self._status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self._status_code >= 400:
            raise Exception(f"HTTP {self._status_code}")
