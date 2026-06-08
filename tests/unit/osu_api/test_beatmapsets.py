import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_helpers import _get_beatmapset_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_beatmapset_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmapset_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        with patch('app.osu_api.client.osu_api_client.Beatmapset') as mock_beatmapset:
            mock_beatmapset.model_validate.return_value = MagicMock()
            mock_beatmapset.model_validate.return_value.serialize.return_value = mock_data
            mock_beatmapset.model_validate.return_value.model_dump.return_value = {"mode": "json"}

            result = await api_client_obj.get_beatmapset(mock_data["id"])

        assert result["id"] == mock_data["id"]
