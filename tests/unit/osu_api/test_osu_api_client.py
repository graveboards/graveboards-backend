import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from app.fixtures.manager import FixtureManager
from tests.unit.osu_api.test_helpers import _get_beatmap_with_fallback, _get_beatmapset_with_fallback
from tests.unit.osu_api.conftest import MockResponse
from app.osu_api.enums import ScoreType, Ruleset


@pytest.fixture(autouse=True)
def mock_rate_limit_decorator():
    from app.osu_api.client import osu_api_client
    with patch.object(osu_api_client, 'rate_limit', lambda *args, **kwargs: lambda func: func):
        yield


@pytest.mark.asyncio
async def test_get_beatmap_from_redis_cache(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmap_with_fallback(fixture_manager)
    
    from app.redis.models import Beatmap
    beatmap_obj = Beatmap.model_validate(mock_data)
    serialized_beatmap = beatmap_obj.serialize()
    
    async def mock_hgetall(key: str):
        if key == f"cached_beatmap:{mock_data['id']}":
            return serialized_beatmap
        return None
    mock_redis.hgetall = AsyncMock(side_effect=mock_hgetall)
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_beatmap(mock_data["id"])
    
    assert result["id"] == mock_data["id"]


@pytest.mark.asyncio
async def test_get_beatmap_from_api(api_client):
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
async def test_get_beatmap_caches_response(api_client):
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
            mock_beatmap_instance = MagicMock()
            mock_beatmap_instance.model_validate.return_value = mock_beatmap_instance
            mock_beatmap_instance.serialize.return_value = mock_data
            mock_beatmap_instance.model_dump.return_value = {"mode": "json"}
            mock_beatmap.model_validate.return_value = mock_beatmap_instance
            
            await api_client_obj.get_beatmap(mock_data["id"])
        
        assert mock_redis.hset.called
        assert mock_redis.expire.called


@pytest.mark.asyncio
async def test_get_beatmap_scores(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "scores": [{"score_id": 1}, {"score_id": 2}],
        "users": [{"user_id": 123, "username": "test"}]
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_beatmap_scores(123, limit=10, offset=5)
        
        assert len(result["scores"]) == 2
        assert result["users"][0]["username"] == "test"


@pytest.mark.asyncio
async def test_get_beatmap_attributes(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "attributes": {
            "difficulty": 5.5,
            "max_combo": 100
        }
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_beatmap_attributes(123, mods=[32])
        
        assert result["attributes"]["difficulty"] == 5.5


@pytest.mark.asyncio
async def test_get_beatmapset_from_redis_cache(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmapset_with_fallback(fixture_manager)
    
    from app.redis.models import Beatmapset
    beatmapset_obj = Beatmapset.model_validate(mock_data)
    serialized_beatmapset = beatmapset_obj.serialize()
    
    async def mock_hgetall(key: str):
        if key == "osu_client_oauth_token":
            return None
        if key == f"cached_beatmapset:{mock_data['id']}":
            return serialized_beatmapset
        return None
    mock_redis.hgetall = AsyncMock(side_effect=mock_hgetall)
    
    # Mock httpx to avoid real API calls
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_beatmapset(mock_data["id"])
    
    assert result["id"] == mock_data["id"]


@pytest.mark.asyncio
async def test_get_beatmapset_from_api(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = _get_beatmapset_with_fallback(fixture_manager)
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        with patch('app.osu_api.client.osu_api_client.Beatmapset') as mock_beatmapset:
            mock_beatmapset_instance = MagicMock()
            mock_beatmapset_instance.model_validate.return_value = mock_beatmapset_instance
            mock_beatmapset_instance.serialize.return_value = mock_data
            mock_beatmapset_instance.model_dump.return_value = {"mode": "json"}
            mock_beatmapset.model_validate.return_value = mock_beatmapset_instance
            
            result = await api_client_obj.get_beatmapset(mock_data["id"])
        
        assert result["id"] == mock_data["id"]
        mock_client_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_user(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "id": 123,
        "username": "test_user",
        "country_code": "US",
        "statistics": {
            "rank": 1000,
            "pp": 3000
        }
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_user(123, mode=Ruleset.OSU)
        
        assert result["id"] == 123
        assert result["username"] == "test_user"


@pytest.mark.asyncio
async def test_get_user_scores(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "scores": [{"score_id": 1}, {"score_id": 2}],
        "users": [{"user_id": 123, "username": "test"}]
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_user_scores(
            123,
            score_type=ScoreType.BEST,
            limit=10
        )
        
        assert len(result["scores"]) == 2


@pytest.mark.asyncio
async def test_get_tags(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "tags": [
            {"tag": "hard", "count": 100},
            {"tag": "easy", "count": 50}
        ]
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_tags()
        
        assert "tags" in result
        assert len(result["tags"]) == 2


@pytest.mark.asyncio
async def test_get_rankings(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "rankings": [
            {"user": {"id": 1, "username": "top1"}, "rank": 1, "pp": 9000},
            {"user": {"id": 2, "username": "top2"}, "rank": 2, "pp": 8500}
        ],
        "total": 10000
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_rankings(
            ruleset=Ruleset.OSU,
            mode="std",
            limit=50,
            cursor_page=1
        )
        
        assert "rankings" in result
        assert len(result["rankings"]) == 2
        assert result["total"] == 10000


@pytest.mark.asyncio
async def test_get_beatmapset_discussions(api_client):
    api_client_obj, mock_redis = api_client
    
    mock_data = {
        "beatmapsets": [
            {"id": 1, "title": "song1"},
            {"id": 2, "title": "song2"}
        ],
        "cursor": {"page": 1}
    }
    
    mock_redis.hgetall.return_value = None
    
    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance
        
        result = await api_client_obj.get_beatmapset_discussions(
            beatmapset_status="ranked",
            page=1,
            limit=50
        )
        
        assert "beatmapsets" in result
        assert len(result["beatmapsets"]) == 2
