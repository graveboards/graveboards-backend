import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from app.fixtures.reader import FixtureReader
from tests.unit.osu_api.test_helpers import _get_beatmap_scores_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_beatmap_scores(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureReader()
    mock_data = _get_beatmap_scores_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.get = AsyncMock(return_value=mock_response)

    result = await api_client_obj.get_beatmap_scores(mock_data["scores"][0]["beatmap_id"], limit=50)

    assert "scores" in result
    assert len(result["scores"]) >= 1


@pytest.mark.asyncio
async def test_get_beatmap_scores_with_offset(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureReader()
    mock_data = _get_beatmap_scores_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.get = AsyncMock(return_value=mock_response)

    await api_client_obj.get_beatmap_scores(mock_data["scores"][0]["beatmap_id"], limit=50, offset=10)
    called_url = str(api_client_obj._http_client.get.call_args[0][0])
    assert "offset=10" in called_url
