import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_utils import _create_mock_tags, _create_mock_rankings_user
from tests.unit.osu_api.test_helpers import _get_user_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_tags(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = _create_mock_tags()

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.get = AsyncMock(return_value=mock_response)

    result = await api_client_obj.get_tags()

    assert "tags" in result
    assert len(result["tags"]) >= 1


@pytest.mark.asyncio
async def test_get_rankings(api_client):
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    mock_data = {
    "rankings": [_create_mock_rankings_user()],
    "score_count": 1,
    }

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.get = AsyncMock(return_value=mock_response)

    result = await api_client_obj.get_rankings(Ruleset.OSU, "performance", limit=50)

    assert "rankings" in result
    assert len(result["rankings"]) >= 1
    assert "score_count" in result


@pytest.mark.asyncio
async def test_get_rankings_with_country_mode(api_client):
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    mock_data = {
    "ranking": [_create_mock_rankings_user()],
    }

    mock_redis.hgetall.return_value = None

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.get = AsyncMock(return_value=mock_response)

    result = await api_client_obj.get_rankings(Ruleset.OSU, "country", limit=50)

    assert "ranking" in result
    assert "country_code" in result["ranking"][0]


@pytest.mark.asyncio
async def test_get_rankings_includes_limit_and_offset(api_client):
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_user_with_fallback(fixture_manager, ruleset="osu")

    mock_redis.hgetall.return_value = None

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.get = AsyncMock(return_value=mock_response)

    await api_client_obj.get_rankings(Ruleset.OSU, "performance", limit=100, offset=50)
    called_url = str(api_client_obj._http_client.get.call_args[0][0])
    assert "limit=100" in called_url
    assert "offset=50" in called_url
