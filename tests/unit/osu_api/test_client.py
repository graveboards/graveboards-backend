import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.fixtures.osu import (
    load_beatmap,
    load_beatmapset,
    load_user,
    load_user_scores_best,
    load_user_scores_recent,
    load_user_scores_firsts,
    load_beatmap_scores,
    load_beatmap_attributes,
    load_rankings,
    load_tags,
)


@pytest.fixture(autouse=True)
def mock_rate_limit_decorator():
    with patch('app.osu_api.client.osu_api_client.rate_limit', lambda *args, **kwargs: lambda func: func):
        yield


@pytest.fixture
def api_client():
    from app.osu_api.client.osu_api_client import OsuAPIClient

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
    mock_data = load_beatmap("beatmap_116383")

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

        assert result["id"] == 116383
        assert result["version"] == "Ridiculousness"
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


@pytest.mark.asyncio
async def test_get_beatmapset_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_beatmapset("beatmapset_35965")

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

            result = await api_client_obj.get_beatmapset(35965)

        assert result["id"] == 35965


@pytest.mark.asyncio
async def test_get_user_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_user("mania/user_7695647_mania")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user(7695647, mode=None)

        assert result["id"] == 7695647
        assert result["username"] == "carlosdaniel100"


@pytest.mark.asyncio
async def test_get_user_scores(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    mock_data = load_user_scores_best("scores_2666342_best")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(2666342, ScoreType.BEST, mode=Ruleset.OSU, limit=50)

        assert len(result) >= 1
        assert result[0]["id"] == 1207011572


@pytest.mark.asyncio
async def test_get_user_scores_recent(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    mock_data = load_user_scores_recent("scores_15296720_recent")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(15296720, ScoreType.RECENT, mode=Ruleset.OSU)

        assert len(result) >= 1
        assert "type" in result[0]


@pytest.mark.asyncio
async def test_get_user_scores_firsts(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    mock_data = load_user_scores_firsts("scores_8558031_firsts")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_user_scores(8558031, ScoreType.FIRSTS, mode=Ruleset.OSU)

        assert len(result) >= 1
        assert "perfect" in result[0]


@pytest.mark.asyncio
async def test_get_beatmap_scores(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_beatmap_scores("scores_116383")

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
async def test_get_beatmap_scores_with_offset(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_beatmap_scores("scores_116383")

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        await api_client_obj.get_beatmap_scores(116383, limit=50, offset=10)

        mock_client_instance.get.assert_called_once()
        called_url = str(mock_client_instance.get.call_args[0][0])
        assert "offset=10" in called_url


@pytest.mark.asyncio
async def test_get_beatmap_attributes(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_beatmap_attributes("beatmap_attrs_69967_mods1")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_beatmap_attributes(69967, [1])

        assert "attributes" in result
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_all_mods(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_beatmap_attributes("beatmap_attrs_69967_mods1")

    mock_redis.hgetall.return_value = None
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        test_attributes = await api_client_obj.get_beatmap_attributes(69967, [16, 64, 128, 256, 512, 1024, 2048, 4096])

        assert "attributes" in test_attributes
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_verifies_mods_in_body(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_beatmap_attributes("beatmap_attrs_69967_mods1")

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        mods = [16, 64]
        await api_client_obj.get_beatmap_attributes(69967, mods)

        post_call = mock_client_instance.post.call_args
        assert post_call[1]["json"]["mods"] == mods


@pytest.mark.asyncio
async def test_get_tags(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = load_tags()

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
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    mock_data = load_rankings("rankings_performance_osu")

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

        assert "rankings" in result
        assert len(result["rankings"]) >= 1
        assert "score_count" in result


@pytest.mark.asyncio
async def test_get_rankings_with_country_mode(api_client):
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    mock_data = load_rankings("rankings_country_osu")

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        result = await api_client_obj.get_rankings(Ruleset.OSU, "country", limit=50)

        assert "ranking" in result
        assert "country_code" in result["ranking"][0]


@pytest.mark.asyncio
async def test_get_rankings_includes_limit_and_offset(api_client):
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    mock_data = load_rankings("rankings_performance_osu")

    mock_redis.hgetall.return_value = None

    with patch('app.osu_api.client.osu_api_client.httpx.AsyncClient') as mock_client_class:
        mock_response = MockResponse(mock_data)
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        await api_client_obj.get_rankings(Ruleset.OSU, "performance", limit=100, offset=50)

        mock_client_instance.get.assert_called_once()
        called_url = str(mock_client_instance.get.call_args[0][0])
        assert "limit=100" in called_url
        assert "offset=50" in called_url
