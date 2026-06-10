import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_helpers import _get_user_with_fallback, _get_scores_with_fallback
from tests.unit.osu_api.conftest import MockResponse


@pytest.mark.asyncio
async def test_get_user_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_user_with_fallback(fixture_manager, ruleset="osu")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user(mock_data["id"], mode=None)

        assert result["id"] == mock_data["id"]
        assert result["username"] == mock_data["username"]


@pytest.mark.asyncio
async def test_get_user_scores(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    fixture_manager = FixtureManager()
    mock_data = _get_scores_with_fallback(fixture_manager, score_type="best")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(mock_data[0]["user_id"], ScoreType.BEST, mode=Ruleset.OSU, limit=50)

        assert len(result) >= 1


@pytest.mark.asyncio
async def test_get_user_scores_recent(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    fixture_manager = FixtureManager()
    mock_data = _get_scores_with_fallback(fixture_manager, score_type="recent")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(mock_data[0]["user_id"], ScoreType.RECENT, mode=Ruleset.OSU)

        assert len(result) >= 1
        assert "type" in result[0]


@pytest.mark.asyncio
async def test_get_user_scores_firsts(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    fixture_manager = FixtureManager()
    mock_data = _get_scores_with_fallback(fixture_manager, score_type="firsts")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(mock_data[0]["user_id"], ScoreType.FIRSTS, mode=Ruleset.OSU)

        assert len(result) >= 1
        assert "perfect" in result[0]
