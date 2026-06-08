import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_helpers import _get_beatmap_scores_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_beatmap_scores(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_scores_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_beatmap_scores(mock_data["scores"][0]["beatmap_id"], limit=50)

        assert "scores" in result
        assert len(result["scores"]) >= 1


@pytest.mark.asyncio
async def test_get_beatmap_scores_with_offset(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_scores_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        await api_client_obj.get_beatmap_scores(mock_data["scores"][0]["beatmap_id"], limit=50, offset=10)

        mock_client_instance.get.assert_called_once()
        called_url = str(mock_client_instance.get.call_args[0][0])
        assert "offset=10" in called_url
