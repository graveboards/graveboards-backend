import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.fixture(autouse=True)
def mock_rate_limit_decorator():
    with patch('app.osu_api.client.osu_api_client.rate_limit', lambda *args, **kwargs: lambda func: func):
        yield


@pytest.fixture
def api_client():
    from app.osu_api.client.osu_api_client import OsuAPIClient
    from app.redis import RedisClient

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


@pytest.mark.asyncio
async def test_get_beatmap_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "beatmap_id": 116383,
        "beatmapset_id": 35965,
        "title": "Event Horizon",
        "creator": "Alexstrasza",
        "version": "Ridiculousness",
        "difficulty_rating": 4.22524,
        "id": 116383,
        "mode": "osu",
        "status": "graveyard",
        "total_length": 141,
        "user_id": 1059782,
        "accuracy": 7,
        "ar": 6,
        "bpm": 87.5,
        "cs": 5,
        "drain": 7,
        "passcount": 3,
        "playcount": 17,
        "ranked": -2,
        "url": "https://osu.ppy.sh/beatmaps/116383",
        "checksum": "d17cf8660c7662d7e606dd395cf1a0a2",
        "count_circles": 202,
        "count_sliders": 118,
        "count_spinners": 4,
        "hit_length": 135,
        "is_scoreable": False,
        "last_updated": "2014-03-10T16:31:10Z",
        "mode_int": 0,
    }

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

            result = await api_client_obj.get_beatmap(116383)

        assert result["beatmap_id"] == 116383
        assert result["title"] == "Event Horizon"
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
async def test_get_beatmapset_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "beatmapset_id": 116383,
        "id": 116383,
        "title": "Event Horizon",
        "artist": "Darius",
        "creator": "Alexstrasza",
    }

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

            result = await api_client_obj.get_beatmapset(116383)

        assert result["beatmapset_id"] == 116383


@pytest.mark.asyncio
async def test_get_user_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "user_id": 11544763,
        "username": "Nivera",
        "accuracy": 95.5,
        "pp_rank": 1000,
        "total_score": 10000000,
    }

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user(11544763)

        assert result["user_id"] == 11544763
        assert result["username"] == "Nivera"


@pytest.mark.asyncio
async def test_get_user_scores(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset
    
    mock_data = [{
        "score_id": 111,
        "max_combo": 300,
        "rank": "SS",
    }]

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(11544763, ScoreType.BEST, mode=Ruleset.OSU, limit=50)

        assert len(result) >= 1


@pytest.mark.asyncio
async def test_get_user_scores_recent(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset
    
    mock_data = [{
        "score_id": 222,
        "type": "solo_score",
        "pp": None,
    }]

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(11544763, ScoreType.RECENT, mode=Ruleset.OSU)

        assert result[0]["type"] == "solo_score"
        assert result[0]["pp"] is None


@pytest.mark.asyncio
async def test_get_user_scores_firsts(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset
    
    mock_data = [{
        "score_id": 333,
        "max_combo": 500,
        "rank": "XH",
        "perfect": True,
        "pp": 1000,
    }]

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(11544763, ScoreType.FIRSTS, mode=Ruleset.OSU)

        assert result[0]["rank"] == "XH"
        assert result[0]["perfect"] is True
        assert result[0]["pp"] == 1000


@pytest.mark.asyncio
async def test_get_beatmap_scores(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "scores": [{
            "score_id": 444,
            "user_id": 999,
        }],
    }

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_beatmap_scores(116383, limit=50)

        assert "scores" in result
        assert len(result["scores"]) >= 1


@pytest.mark.asyncio
async def test_get_beatmap_attributes(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "attributes": {
            "difficulty": 5.5,
            "max_combo": 100,
        }
    }

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_beatmap_attributes(2150839, [])

        assert result["attributes"]["difficulty"] > 0
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_all_mods(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "attributes": {
            "difficulty": 7.5,
            "max_combo": 150,
        }
    }

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        test_attributes = await api_client_obj.get_beatmap_attributes(2150839, [16, 64, 128, 256, 512, 1024, 2048, 4096])

        assert test_attributes["attributes"]["difficulty"] > 0
        assert test_attributes["attributes"]["max_combo"] > 0


@pytest.mark.asyncio
async def test_get_tags(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "tags": ["tag1", "tag2", "tag3"],
    }

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_tags()

        assert "tags" in result
        assert len(result["tags"]) >= 1


@pytest.mark.asyncio
async def test_get_rankings(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = {
        "ranking": [{
            "user_id": 111,
            "rank": 1,
            "score": 1000000,
        }],
        "total": 100,
    }
    from app.osu_api.enums import Ruleset

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_rankings(Ruleset.OSU, "performance", limit=50)

        assert "ranking" in result
        assert "total" in result
        assert len(result["ranking"]) >= 1
