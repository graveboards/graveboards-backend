import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.unit.osu_api.test_utils import (
    _create_mock_beatmap,
    _create_mock_beatmapset,
    _create_mock_user,
    _create_mock_score,
    _create_mock_beatmap_scores,
    _create_mock_beatmap_attributes,
    _create_mock_tags,
    _create_mock_rankings_user,
)
from tests.unit.osu_api.test_helpers import (
    _get_beatmap_with_fallback,
    _get_beatmapset_with_fallback,
    _get_user_with_fallback,
    _get_scores_with_fallback,
    _get_beatmap_scores_with_fallback,
    _get_beatmap_attributes_with_fallback,
)


@pytest.fixture(autouse=True)
def mock_rate_limit_decorator():
    with patch('app.osu_api.client.osu_api_client.rate_limit', lambda *args, **kwargs: lambda func: func):
        yield


@pytest.fixture
def api_client():
    from app.osu_api.client.osu_api_client import OsuAPIClient

    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.lock_ctx = MagicMock()
    mock_redis.lock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_redis.lock_ctx.__aexit__ = AsyncMock(return_value=None)

    client = OsuAPIClient(mock_redis)
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
