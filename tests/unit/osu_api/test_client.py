import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.fixtures.osu import FixtureManager


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
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmap_by_id(116383)
    if not mock_data:
        mock_data = {
            "id": 116383,
            "beatmapset_id": 35965,
            "checksum": None,
            "filename": "test.osu",
            "total_length": 180,
            "hit_length": 180,
            "difficulty_rating": 5.5,
            "mode": 0,
            "allow_mania": False,
            "convert": False,
            "count_circles": 100,
            "count_sliders": 50,
            "count_spinners": 10,
            "last_modified": "2024-01-01T00:00:00Z",
            "status": "ranked",
            "mode_int": 0,
            "ar": 9.5,
            "cs": 4.0,
            "hp": 7.0,
            "od": 8.0,
            "slider_multiplier": 1.0,
            "slider_tick_rate": 1,
            "ruleset_id": 0,
            "version": "Ridiculousness",
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
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmapset_by_id(35965)
    if not mock_data:
        mock_data = {
            "id": 35965,
            "title": "Test Song",
            "artist": "Test Artist",
            "creator": "Test Creator",
            "cover": "cover.jpg",
            "favourite_count": 100,
            "playcount": 10000,
            "status": "ranked",
            "beatmaps": [],
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

            result = await api_client_obj.get_beatmapset(35965)

        assert result["id"] == 35965


@pytest.mark.asyncio
async def test_get_user_parses_response(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_user_by_id(7695647, "mania")
    if not mock_data:
        mock_data = {
            "id": 7695647,
            "username": "carlosdaniel100",
            "avatar_url": "avatar.jpg",
            "country": "BR",
            "country_code": "BR",
            "cover_url": "cover.jpg",
            "custom_url": "user/carlosdaniel100",
            "is_admin": False,
            "is_supporter": False,
            "last_visit": "2024-01-01T00:00:00Z",
            "profile_order": [],
            "title_id": None,
            "user_achievements": [],
            "user_level": 50,
            "user_preferences": {},
            "user_profile_background": None,
            "user_rank": 1000,
            "user_statistics": {
                "rank": 1000,
                "country_rank": 100,
                "pp": 3000,
                "grade_counts": {"ss": 10, "s": 50, "a": 100},
                "play_count": 10000,
                "play_time": 500000,
                "total_score": 10000000,
                "total_hits": 500000,
                "maximum_combo": 500,
                "rank": {"osu": 1000, "taiko": None, "fruits": None, "mania": None},
                "pp_breakdown": {},
                "replay_popularity": 100,
                "rank_history": {"mode": "osu", "data": []},
                "ranked_score": 10000000,
                "hits": 500000,
                "accuracy": 95.0,
            },
            "username_change_enabled": True,
            "email": "test@example.com",
            "is_active": True,
            "is_bot": False,
            "is_deleted": False,
            "is_online": True,
            "is_presumed_invisible": False,
            "permissions": {},
            "profile_colour": None,
            "can_be_deleted": True,
            "can_be_updated": True,
            "can_make_supporter": True,
            "country": {"code": "BR", "name": "Brazil"},
            "cover": {"custom_url": None, "url": "cover.jpg", "id": None},
            "is_restricted": False,
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

        result = await api_client_obj.get_user(7695647, mode=None)

        assert result["id"] == 7695647
        assert result["username"] == "carlosdaniel100"


@pytest.mark.asyncio
async def test_get_user_scores(api_client):
    api_client_obj, mock_redis = api_client
    from app.osu_api.enums import ScoreType, Ruleset

    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_scores("best", count=1)
    if not mock_data:
        mock_data = [
            {
                "id": 1207011572,
                "user_id": 2666342,
                "beatmap_id": 116383,
                "rank": "S",
                "pp": 450.0,
                "score": 950000,
                "max_combo": 500,
                "count_50": 0,
                "count_100": 10,
                "count_300": 200,
                "count_miss": 0,
                "count_katus": 5,
                "count_geki": 10,
                "perfect": True,
                "mods": [],
                "pass": True,
                "created_at": "2024-01-01T00:00:00Z",
                "user": {
                    "id": 2666342,
                    "username": "test_user",
                    "country": "US",
                },
            },
        ]

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

    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_scores("recent", count=1)
    if not mock_data:
        mock_data = [
            {
                "id": 15296720,
                "user_id": 15296720,
                "beatmap_id": 116383,
                "rank": "S",
                "pp": 400.0,
                "score": 900000,
                "max_combo": 450,
                "count_50": 0,
                "count_100": 20,
                "count_300": 180,
                "count_miss": 0,
                "count_katus": 10,
                "count_geki": 5,
                "perfect": False,
                "mods": [],
                "pass": True,
                "created_at": "2024-01-01T00:00:00Z",
                "type": "classic",
                "user": {
                    "id": 15296720,
                    "username": "test_user2",
                    "country": "US",
                },
            },
        ]

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

    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_scores("firsts", count=1)
    if not mock_data:
        mock_data = [
            {
                "id": 8558031,
                "user_id": 8558031,
                "beatmap_id": 116383,
                "rank": "SH",
                "pp": 480.0,
                "score": 980000,
                "max_combo": 520,
                "count_50": 0,
                "count_100": 5,
                "count_300": 210,
                "count_miss": 0,
                "count_katus": 0,
                "count_geki": 15,
                "perfect": True,
                "mods": [],
                "pass": True,
                "created_at": "2024-01-01T00:00:00Z",
                "user": {
                    "id": 8558031,
                    "username": "test_user3",
                    "country": "US",
                },
            },
        ]

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
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmap_scores_by_beatmap(116383)
    if not mock_data:
        mock_data = {
            "scores": [
                {
                    "id": 116383,
                    "user_id": 123456,
                    "beatmap_id": 116383,
                    "rank": "S",
                    "pp": 380.0,
                    "score": 850000,
                    "max_combo": 400,
                    "count_50": 0,
                    "count_100": 15,
                    "count_300": 150,
                    "count_miss": 5,
                    "count_katus": 10,
                    "count_geki": 5,
                    "perfect": False,
                    "mods": [],
                    "pass": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "user": {
                        "id": 123456,
                        "username": "test_user",
                        "country": "US",
                    },
                },
            ],
            "user_score": None,
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
async def test_get_beatmap_scores_with_offset(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmap_scores_by_beatmap(116383)
    if not mock_data:
        mock_data = {
            "scores": [
                {
                    "id": 116383,
                    "user_id": 123456,
                    "beatmap_id": 116383,
                    "rank": "S",
                    "pp": 380.0,
                    "score": 850000,
                    "max_combo": 400,
                    "count_50": 0,
                    "count_100": 15,
                    "count_300": 150,
                    "count_miss": 5,
                    "count_katus": 10,
                    "count_geki": 5,
                    "perfect": False,
                    "mods": [],
                    "pass": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "user": {
                        "id": 123456,
                        "username": "test_user",
                        "country": "US",
                    },
                },
            ],
            "user_score": None,
        }

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
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmap_attributes_by_beatmap(69967)
    if not mock_data:
        mock_data = {
            "attributes": {
                "AR": 9.5,
                "CS": 4.0,
                "HP": 7.0,
                "OD": 8.0,
                "slider_tick_rate": 1,
                "slider_multiplier": 1.0,
                "spins": [
                    {
                        "spin_type": "fast_spin",
                        "required_hits": 3,
                    },
                ],
            },
            "mods": [1],
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

        result = await api_client_obj.get_beatmap_attributes(69967, [1])

        assert "attributes" in result
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_all_mods(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmap_attributes_by_beatmap(69967)
    if not mock_data:
        mock_data = {
            "attributes": {
                "AR": 9.5,
                "CS": 4.0,
                "HP": 7.0,
                "OD": 8.0,
                "slider_tick_rate": 1,
                "slider_multiplier": 1.0,
                "spins": [
                    {
                        "spin_type": "fast_spin",
                        "required_hits": 3,
                    },
                ],
            },
            "mods": [16, 64, 128, 256, 512, 1024, 2048, 4096],
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

        test_attributes = await api_client_obj.get_beatmap_attributes(69967, [16, 64, 128, 256, 512, 1024, 2048, 4096])

        assert "attributes" in test_attributes
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_beatmap_attributes_verifies_mods_in_body(api_client):
    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = fixture_manager.get_beatmap_attributes_by_beatmap(69967)
    if not mock_data:
        mock_data = {
            "attributes": {
                "AR": 9.5,
                "CS": 4.0,
                "HP": 7.0,
                "OD": 8.0,
                "slider_tick_rate": 1,
                "slider_multiplier": 1.0,
                "spins": [
                    {
                        "spin_type": "fast_spin",
                        "required_hits": 3,
                    },
                ],
            },
            "mods": [16, 64],
        }

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
    fixture_manager = FixtureManager()
    mock_data = fixture_manager._get_fixture_by_id("tags", "tags", prefix="tags")
    if not mock_data:
        mock_data = {
            "tags": [
                "osu", "taiko", "fruits", "mania",
                "easy", "medium", "hard", "expert",
                "chill", "intense", "relaxing", "energetic",
                "vocal", "instrumental", "rock", "electronic",
            ],
            "category": "gameplay",
            "last_updated": "2024-01-01T00:00:00Z",
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
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = fixture_manager._get_fixture_by_id("rankings", "rankings_performance_osu", prefix="rankings_performance_osu")
    if not mock_data:
        mock_data = {
            "rankings": [
                {
                    "user": {
                        "id": 12345,
                        "username": "top_player",
                        "country": "US",
                        "country_code": "US",
                    },
                    "rank": 1,
                    "pp": 9000,
                    "score": 10000000,
                    "rank_history": {"data": [900, 920, 950]},
                },
            ],
            "offset": 0,
            "score_count": 100,
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

        result = await api_client_obj.get_rankings(Ruleset.OSU, "performance", limit=50)

        assert "rankings" in result
        assert len(result["rankings"]) >= 1
        assert "score_count" in result


@pytest.mark.asyncio
async def test_get_rankings_with_country_mode(api_client):
    from app.osu_api.enums import Ruleset

    api_client_obj, mock_redis = api_client
    fixture_manager = FixtureManager()
    mock_data = fixture_manager._get_fixture_by_id("rankings", "rankings_country_osu", prefix="rankings_country_osu")
    if not mock_data:
        mock_data = {
            "ranking": [
                {
                    "user": {
                        "id": 12345,
                        "username": "top_player",
                        "country": "US",
                        "country_code": "US",
                    },
                    "rank": 1,
                    "pp": 9000,
                    "score": 10000000,
                    "rank_history": {"data": [900, 920, 950]},
                    "country_code": "US",
                },
            ],
            "offset": 0,
        }

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
    fixture_manager = FixtureManager()
    mock_data = fixture_manager._get_fixture_by_id("rankings", "rankings_performance_osu", prefix="rankings_performance_osu")
    if not mock_data:
        mock_data = {
            "ranking": [
                {
                    "user": {
                        "id": 12345,
                        "username": "top_player",
                        "country": "US",
                        "country_code": "US",
                    },
                    "rank": 1,
                    "pp": 9000,
                    "score": 10000000,
                    "rank_history": {"data": [900, 920, 950]},
                },
            ],
            "offset": 50,
        }

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
