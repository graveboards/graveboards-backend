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


def _create_mock_beatmap(**overrides):
    mock_data = {
        "id": 100001,
        "beatmapset_id": 10000,
        "status": "ranked",
        "ruleset_id": 0,
        "difficulty_rating": 4.5,
        "version": "Hard",
        "accuracy": 95.0,
        "ar": 9.0,
        "bpm": 120.0,
        "cs": 4.0,
        "drain": 5.0,
        "hit_length": 180,
        "mode": 0,
        "passcount": 100,
        "playcount": 1000,
        "max_combo": 500,
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_beatmapset(**overrides):
    mock_data = {
        "id": 10000,
        "status": "ranked",
        "user_id": 1000,
        "title": "Test Song",
        "creator": "Test Creator",
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_user(ruleset="osu", **overrides):
    mock_data = {
        "id": 200001,
        "username": "test_user",
        "country": "US",
        "country_code": "US",
        "avatar_url": "https://example.com/avatar.png",
        "cover_url": "https://example.com/cover.png",
        "custom_url": "test_user",
        "is_active": True,
        "is_bot": False,
        "is_deleted": False,
        "is_supporter": False,
        "last_visit": "2024-01-01T00:00:00Z",
        "pm_friends_only": False,
        "profile_order": [],
        "title_id": None,
        "user_color": None,
        "ruleset": ruleset,
        "statistics": {
            "level": {
                "current": 50,
                "progress": 50,
            },
            "play_count": 10000,
            "rank": {
                "country": 100,
            },
            "pp": 1000.0,
            "accuracy": 95.0,
            "total_score": 10000000,
            "total_hits": 1000000,
            "maximum_combo": 5000,
            "replays_watched_by_others": 100,
            "grade_counts": {
                "ss": 10,
                "s": 50,
                "a": 100,
            },
            "rank": {
                "country": 100,
            },
        },
        "rank_highest": {
            "rank": 100,
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "created_at": "2020-01-01T00:00:00Z",
        "friends": [],
        "interests": [],
        " occupation": "",
        "location": "",
        "total_seconds_used": 100000,
        "pending_marketplace_placements": False,
        "signature": "",
        "avatar_lock_status": None,
        "avatar_lock_reason": None,
        "github": "",
        "discord": "",
        "website": "",
        "donation_level": 0,
        "change_name_history": [],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_score(**overrides):
    mock_data = {
        "id": 300001,
        "user_id": 200001,
        "beatmap_id": 100001,
        "rank": "S",
        "mods": [4, 16],
        "score": 950000,
        "max_combo": 500,
        "perfect": True,
        "type": "best",
        "statistics": {
            "count_50": 0,
            "count_100": 10,
            "count_300": 300,
            "count_geki": 10,
            "count_katsu": 5,
            "count_miss": 0,
        },
        "total_score": 950000,
        "pp": 200.0,
        "weight": {
            "percentage": 100.0,
            "pp": 200.0,
        },
        "start_time": "2024-01-01T00:00:00Z",
        "ended_at": "2024-01-01T00:03:00Z",
        "comment": "",
        "mod": ["HR", "HD"],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_beatmap_scores(beatmap_id=None, **overrides):
    if beatmap_id is None:
        beatmap_id = 100001
    mock_data = {
        "beatmap_id": beatmap_id,
        "scores": [
            {
                "id": 300001,
                "user_id": 200001,
                "beatmap_id": beatmap_id,
                "rank": "S",
                "mods": [4, 16],
                "score": 950000,
                "max_combo": 500,
                "perfect": True,
                "statistics": {
                    "count_50": 0,
                    "count_100": 10,
                    "count_300": 300,
                    "count_geki": 10,
                    "count_katsu": 5,
                    "count_miss": 0,
                },
                "total_score": 950000,
                "pp": 200.0,
                "weight": {
                    "percentage": 100.0,
                    "pp": 200.0,
                },
                "start_time": "2024-01-01T00:00:00Z",
                "ended_at": "2024-01-01T00:03:00Z",
                "comment": "",
                "mod": ["HR", "HD"],
            }
        ],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_beatmap_attributes(beatmap_id=None, **overrides):
    if beatmap_id is None:
        beatmap_id = 100001
    mock_data = {
        "attributes": {
            "beatmap_id": beatmap_id,
            "difficulty_rating": 4.5,
            "total_length": 180,
            "user_id": 1000,
            "version": "Hard",
            "accuracy": 95.0,
            "ar": 9.0,
            "bpm": 120.0,
            "cs": 4.0,
            "drain": 5.0,
            "count_circles": 100,
            "count_sliders": 50,
            "count_spinners": 10,
            "max_combo": 500,
            "mode": 0,
            "tags": ["test", "easy"],
            "favourite_count": 100,
            "playcount": 1000,
            "passcount": 100,
            "allow_custom_difficulty": True,
            "allow UserModel": True,
            "allow UserModel_scores": True,
            "allow UserModel_mods": True,
            "allow UserModel_leaderboard": True,
            "allow UserModel_chat": True,
            "allow UserModel_report": True,
            "allow UserModel_moderation": True,
            "allow UserModel_admin": True,
            "allow UserModel_system": True,
            "allow UserModel_donation": True,
            "allow UserModel_supporter": True,
            "allow UserModel_patron": True,
            "allow UserModel_veteran": True,
            "allow UserModel_contributor": True,
            "allow UserModel_developer": True,
            "allow UserModel_maintainer": True,
            "allow UserModel_mod": True,
            "allow UserModel_editor": True,
            "allow UserModel_beta": True,
            "allow UserModel_alpha": True,
            "allow UserModel_dev": True,
            "allow UserModel_admin": True,
            "allow UserModel_sys": True,
            "allow UserModel_don": True,
            "allow UserModel_sup": True,
            "allow UserModel_pat": True,
            "allow UserModel_vet": True,
            "allow UserModel_con": True,
            "allow UserModel_dev": True,
            "allow UserModel_mod": True,
            "allow UserModel_ed": True,
            "allow UserModel_bet": True,
            "allow UserModel_alp": True,
        },
        "mods": [16],
        "remaining_beatmapset_locks": 0,
        "remaining_beatmap_locks": 0,
        "remaining_user_locks": 0,
    }
    mock_data.update(overrides)
    return mock_data


def _get_beatmap_with_fallback(fixture_manager):
    beatmaps = fixture_manager.get_beatmaps(by_status=["ranked"], count=1)
    if beatmaps:
        return beatmaps[0]
    else:
        return _create_mock_beatmap()


def _get_beatmapset_with_fallback(fixture_manager):
    beatmapsets = fixture_manager.get_beatmapsets(by_status=["ranked"], count=1)
    if beatmapsets:
        return beatmapsets[0]
    else:
        return _create_mock_beatmapset()


def _get_user_with_fallback(fixture_manager, ruleset="osu"):
    users = fixture_manager.get_users(ruleset=ruleset, count=1)
    if users:
        return users[0]
    else:
        return _create_mock_user(ruleset=ruleset)


def _get_scores_with_fallback(fixture_manager, score_type="best"):
    scores = fixture_manager.get_scores(score_type=score_type, count=1)
    if scores:
        return scores[0]
    else:
        return [_create_mock_score()]


def _get_beatmap_scores_with_fallback(fixture_manager):
    scores = fixture_manager.get_beatmap_scores(count=1)
    if scores:
        return scores[0] if scores else _create_mock_beatmap_scores()
    else:
        return _create_mock_beatmap_scores()


def _get_beatmap_attributes_with_fallback(fixture_manager):
    attrs = fixture_manager.get_beatmap_attributes()
    if attrs:
        return attrs
    else:
        return _create_mock_beatmap_attributes()


def _create_mock_tags(**overrides):
    mock_data = {
        "tags": ["test", "osu", "easy", "mapped"],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_rankings_user(**overrides):
    mock_data = {
        "user_id": 200001,
        "username": "test_user",
        "country": "US",
        "country_code": "US",
        "avatar_url": "https://example.com/avatar.png",
        "cover_url": "https://example.com/cover.png",
        "custom_url": "test_user",
        "is_active": True,
        "is_bot": False,
        "is_deleted": False,
        "is_supporter": False,
        "last_visit": "2024-01-01T00:00:00Z",
        "pm_friends_only": False,
        "profile_order": [],
        "title_id": None,
        "user_color": None,
        "statistics": {
            "play_count": 10000,
            "rank": {
                "country": 100,
            },
            "pp": 1000.0,
            "accuracy": 95.0,
            "total_score": 10000000,
            "total_hits": 1000000,
            "maximum_combo": 5000,
            "replays_watched_by_others": 100,
            "grade_counts": {
                "ss": 10,
                "s": 50,
                "a": 100,
            },
        },
        "rank_highest": {
            "rank": 100,
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "created_at": "2020-01-01T00:00:00Z",
        "friends": [],
        "interests": [],
        "occupation": "",
        "location": "",
        "total_seconds_used": 100000,
        "pending_marketplace_placements": False,
        "signature": "",
        "avatar_lock_status": None,
        "avatar_lock_reason": None,
        "github": "",
        "discord": "",
        "website": "",
        "donation_level": 0,
        "change_name_history": [],
    }
    mock_data.update(overrides)
    return mock_data


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


@pytest.mark.asyncio
async def test_get_tags(api_client):
    api_client_obj, mock_redis = api_client
    mock_data = _create_mock_tags()

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
    mock_data = {
        "rankings": [_create_mock_rankings_user()],
        "score_count": 1,
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
    mock_data = {
        "ranking": [_create_mock_rankings_user()],
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
    mock_data = _get_user_with_fallback(fixture_manager, ruleset="osu")

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
