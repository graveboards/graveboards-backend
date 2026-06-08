import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_helpers import _get_beatmap_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_beatmap_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_with_fallback(fixture_manager)

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        with patch('app.osu_api.client.osu_api_client.Beatmap') as mock_beatmap:
            mock_beatmap.model_validate.return_value = MagicMock()
            mock_beatmap.model_validate.return_value.serialize.return_value = mock_data
            mock_beatmap.model_validate.return_value.model_dump.return_value = {"mode": "json"}

            result = await api_client_obj.get_beatmap(mock_data["id"])

        assert result["id"] == mock_data["id"]
        assert result["version"] == mock_data["version"]
        mock_client_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_handles_404(api_client):
    api_client_obj, mock_redis = api_client
    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse({"error": "Not Found"}, status_code=404)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        with pytest.raises(Exception, match="HTTP 404"):
            await api_client_obj.get_beatmap(999999)


@pytest.mark.asyncio
async def test_get_beatmap_handles_rate_limit(api_client):
    api_client_obj, mock_redis = api_client
    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse({"error": "Rate limit exceeded"}, status_code=429)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        with pytest.raises(Exception, match="HTTP 429"):
            await api_client_obj.get_beatmap(116383)


@pytest.mark.asyncio
async def test_get_beatmap_handles_server_error(api_client):
    api_client_obj, mock_redis = api_client
    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse({"error": "Internal Server Error"}, status_code=500)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        with pytest.raises(Exception, match="HTTP 500"):
            await api_client_obj.get_beatmap(116383)
