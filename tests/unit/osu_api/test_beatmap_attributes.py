import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_helpers import _get_beatmap_attributes_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_beatmap_attributes(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_attributes_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.post = AsyncMock(return_value=mock_response)

    result = await api_client_obj.get_beatmap_attributes(mock_data["attributes"]["beatmap_id"], [1])

    assert "attributes" in result


@pytest.mark.asyncio
async def test_get_beatmap_attributes_all_mods(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_attributes_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.post = AsyncMock(return_value=mock_response)

    test_attributes = await api_client_obj.get_beatmap_attributes(mock_data["attributes"]["beatmap_id"], [16, 64, 128, 256, 512, 1024, 2048, 4096])

    assert "attributes" in test_attributes


@pytest.mark.asyncio
async def test_get_beatmap_attributes_verifies_mods_in_body(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_attributes_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None

    mock_response = MockResponse(mock_data)
    api_client_obj._http_client.post = AsyncMock(return_value=mock_response)

    mods = [16, 64]
    await api_client_obj.get_beatmap_attributes(mock_data["attributes"]["beatmap_id"], mods)

    post_call = api_client_obj._http_client.post.call_args
    assert post_call[1]["json"]["mods"] == mods
