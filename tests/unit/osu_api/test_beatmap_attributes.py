import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_beatmap_attributes(mock_data["attributes"]["beatmap_id"], [1])

        assert "attributes" in result
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_all_mods(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_attributes_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        test_attributes = await api_client_obj.get_beatmap_attributes(mock_data["attributes"]["beatmap_id"], [16, 64, 128, 256, 512, 1024, 2048, 4096])

        assert "attributes" in test_attributes
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_verifies_mods_in_body(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_attributes_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        mods = [16, 64]
        await api_client_obj.get_beatmap_attributes(mock_data["attributes"]["beatmap_id"], mods)

        post_call = mock_client_instance.post.call_args
        assert post_call[1]["json"]["mods"] == mods
