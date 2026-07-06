"""Unit tests for Redis model serialization (Beatmap, Beatmapset, OAuthToken, QueueRequestHandlerTask)."""

import pytest
from datetime import datetime

from app.redis.models.beatmap import Beatmap
from app.redis.models.beatmapset import Beatmapset
from app.redis.models.osu_client_oauth_token import OsuClientOAuthToken
from app.redis.models.queue_request_handler_task import QueueRequestHandlerTask


def _full_beatmap_dict():
    return {
        "id": 12345,
        "user_id": 67890,
        "beatmapset_id": 11111,
        "version": "Easy Master",
        "creator": "TestCreator",
        "bpm": 180.0,
        "total_length": 240,
        "hit_length": 216,
        "status": "ranked",
        "difficulty_rating": 7.5,
        "playcount": 5000,
        "passcount": 3000,
        "mode": "osu",
        "mode_int": 0,
        "accuracy": 95.5,
        "ar": 8.0,
        "cs": 4.0,
        "drain": 6.0,
        "count_circles": 200,
        "count_sliders": 100,
        "count_spinners": 5,
        "max_combo": 1500,
        "is_scoreable": True,
        "ranked": 1,
        "url": "https://osu.ppy.sh/beatmaps/12345",
        "checksum": "abc123",
        "failtimes": {"exit": [10, 20], "fail": [30, 40, 50]},
        "last_updated": "2024-06-15T12:00:00+00:00",
        "deleted_at": None,
        "owners": [],
        "top_tag_ids": [],
    }


def _full_beatmapset_dict():
    return {
        "id": 11111,
        "user_id": 67890,
        "title": "Test Song",
        "title_unicode": "Test Song",
        "artist": "Test Artist",
        "artist_unicode": "Test Artist",
        "bpm": 180.0,
        "status": "ranked",
        "ranked": 1,
        "rating": 4.5,
        "source": "",
        "tags": "test tag",
        "pack_tags": [],
        "storyboard": False,
        "spotlight": False,
        "video": False,
        "nsfw": False,
        "can_be_hyped": True,
        "discussion_enabled": True,
        "discussion_locked": False,
        "is_scoreable": True,
        "favourite_count": 100,
        "play_count": 5000,
        "offset": 0,
        "track_id": None,
        "preview_url": "https://example.com/pre.mp3",
        "legacy_thread_url": None,
        "deleted_at": None,
        "ranked_date": None,
        "creator": "TestCreator",
        "beatmaps": [_full_beatmap_dict()],
        "availability": {"download_disabled": False, "more_information": None},
        "covers": {
            "cover": "x100", "cover_2x": "x200",
            "card": "x100", "card_2x": "x200",
            "list": "x100", "list_2x": "x200",
            "slimcover": "x100", "slimcover_2x": "x200",
        },
        "current_nominations": [],
        "description": {"description": ""},
        "genre": None,
        "hype": {"current": 0, "required": 2},
        "language": None,
        "nominations_summary": {
            "current": 0, "eligible_main_rulesets": None,
            "required_meta": {"main_ruleset": 0, "non_main_ruleset": 0},
        },
        "ratings": [],
        "last_updated": "2024-06-15T12:00:00+00:00",
        "submitted_date": "2024-01-01T00:00:00+00:00",
    }


class TestBeatmapSerialization:
    """Test Beatmap model serialization round-trips."""

    def _make_beatmap(self):
        return Beatmap.model_validate(_full_beatmap_dict())

    def test_serialize_returns_string_dict(self):
        """Test Beatmap.serialize() returns dict with all string values."""
        beatmap = self._make_beatmap()
        serialized = beatmap.serialize()
        assert isinstance(serialized, dict)
        for value in serialized.values():
            assert isinstance(value, str)

    def test_serialize_id_as_string(self):
        """Test Beatmap ID is serialized as string."""
        beatmap = self._make_beatmap()
        assert beatmap.serialize()["id"] == "12345"

    def test_serialize_preserves_nested_failtimes(self):
        """Test failtimes serialization preserves structure."""
        beatmap = self._make_beatmap()
        serialized = beatmap.serialize()
        assert "failtimes" in serialized
        assert "exit" in serialized["failtimes"]

    def test_deserialize_roundtrip_preserves_id(self):
        """Test Beatmap round-trip preserves the ID field."""
        beatmap = self._make_beatmap()
        restored = Beatmap.deserialize(beatmap.serialize())
        assert restored.id == 12345

    def test_deserialize_roundtrip_preserves_floats(self):
        """Test Beatmap round-trip preserves float fields."""
        beatmap = self._make_beatmap()
        restored = Beatmap.deserialize(beatmap.serialize())
        assert restored.bpm == 180.0
        assert restored.difficulty_rating == 7.5

    def test_deserialize_roundtrip_preserves_ints(self):
        """Test Beatmap round-trip preserves integer fields."""
        beatmap = self._make_beatmap()
        restored = Beatmap.deserialize(beatmap.serialize())
        assert restored.user_id == 67890
        assert restored.playcount == 5000
        assert restored.passcount == 3000

    def test_serialize_excludes_none_values_as_empty_string(self):
        """Test Beatmap serializes None values as empty strings."""
        d = _full_beatmap_dict()
        d["deleted_at"] = None
        beatmap = Beatmap.model_validate(d)
        assert beatmap.serialize()["deleted_at"] == ""


class TestBeatmapsetSerialization:
    """Test Beatmapset model serialization round-trips."""

    def _make_beatmapset(self):
        return Beatmapset.model_validate(_full_beatmapset_dict())

    def test_serialize_returns_string_dict(self):
        """Test Beatmapset.serialize() returns dict with all string values."""
        bs = self._make_beatmapset()
        serialized = bs.serialize()
        assert isinstance(serialized, dict)
        for value in serialized.values():
            assert isinstance(value, str)

    def test_serialize_nested_beatmaps(self):
        """Test Beatmapset serializes nested beatmaps as string."""
        bs = self._make_beatmapset()
        serialized = bs.serialize()
        assert isinstance(serialized["beatmaps"], str)
        assert "12345" in serialized["beatmaps"]

    def test_deserialize_roundtrip_preserves_id(self):
        """Test Beatmapset round-trip preserves the ID."""
        bs = self._make_beatmapset()
        restored = Beatmapset.deserialize(bs.serialize())
        assert restored.id == 11111

    def test_deserialize_roundtrip_preserves_nested_beatmaps(self):
        """Test Beatmapset round-trip preserves nested beatmaps."""
        bs = self._make_beatmapset()
        restored = Beatmapset.deserialize(bs.serialize())
        assert len(restored.beatmaps) == 1
        assert restored.beatmaps[0].id == 12345


class TestOAuthTokenSerialization:
    """Test OsuClientOAuthToken serialization round-trips."""

    def _make_token(self):
        return OsuClientOAuthToken(
            access_token="test_access_token_abc123",
            token_type="bearer",
            expires_in=5184000,
            expires_at=1735689600,
        )

    def test_serialize_returns_string_dict(self):
        """Test token serializes to all-string dict."""
        token = self._make_token()
        serialized = token.serialize()
        assert isinstance(serialized, dict)
        for value in serialized.values():
            assert isinstance(value, str)

    def test_serialize_preserves_access_token(self):
        """Test token serialization preserves access_token."""
        token = self._make_token()
        assert token.serialize()["access_token"] == "test_access_token_abc123"

    def test_deserialize_roundtrip_preserves_all_fields(self):
        """Test token round-trip preserves all fields."""
        token = self._make_token()
        restored = OsuClientOAuthToken.deserialize(token.serialize())
        assert restored.access_token == "test_access_token_abc123"
        assert restored.token_type == "bearer"
        assert restored.expires_in == 5184000
        assert restored.expires_at == 1735689600

    def test_deserialize_converts_expires_to_int(self):
        """Test token deserialization converts expires_in/expires_at to int."""
        restored = OsuClientOAuthToken.deserialize({
            "access_token": "tok", "token_type": "bearer",
            "expires_in": "5184000", "expires_at": "1735689600",
        })
        assert isinstance(restored.expires_in, int)
        assert isinstance(restored.expires_at, int)


class TestQueueRequestHandlerTaskSerialization:
    """Test QueueRequestHandlerTask serialization round-trips."""

    def _make_task(self):
        return QueueRequestHandlerTask(
            user_id=12345678,
            beatmapset_id=35965,
            queue_id=1,
            comment="Please rank this!",
            mv_checked=False,
        )

    def test_serialize_returns_string_dict(self):
        """Test task serializes to all-string dict."""
        task = self._make_task()
        serialized = task.serialize()
        assert isinstance(serialized, dict)
        for value in serialized.values():
            assert isinstance(value, str)

    def test_serialize_preserves_user_id(self):
        """Test task serialization preserves user_id."""
        task = self._make_task()
        assert task.serialize()["user_id"] == "12345678"

    def test_serialize_preserves_bool_as_string(self):
        """Test task serialization converts bool to string."""
        task = self._make_task()
        assert task.serialize()["mv_checked"] == "False"

    def test_serialize_null_datetimes_as_empty_string(self):
        """Test task serializes None datetimes as empty strings."""
        task = self._make_task()
        assert task.serialize()["completed_at"] == ""
        assert task.serialize()["failed_at"] == ""

    def test_deserialize_roundtrip_preserves_all_fields(self):
        """Test task round-trip preserves all fields."""
        task = self._make_task()
        restored = QueueRequestHandlerTask.deserialize(task.serialize())
        assert restored.user_id == 12345678
        assert restored.beatmapset_id == 35965
        assert restored.queue_id == 1
        assert restored.comment == "Please rank this!"
        assert restored.mv_checked is False

    def test_deserialize_converts_ids_to_int(self):
        """Test task deserialization converts id fields to int."""
        serialized = {
            "user_id": "12345678", "beatmapset_id": "35965", "queue_id": "1",
            "comment": "test", "mv_checked": "False", "completed_at": "", "failed_at": "",
        }
        restored = QueueRequestHandlerTask.deserialize(serialized)
        assert isinstance(restored.user_id, int)
        assert isinstance(restored.beatmapset_id, int)
        assert isinstance(restored.queue_id, int)

    def test_deserialize_null_datetimes_to_none(self):
        """Test task deserialization converts empty datetime strings to None."""
        serialized = {
            "user_id": "1", "beatmapset_id": "2", "queue_id": "3",
            "comment": "test", "mv_checked": "False", "completed_at": "", "failed_at": "",
        }
        restored = QueueRequestHandlerTask.deserialize(serialized)
        assert restored.completed_at is None
        assert restored.failed_at is None

    def test_deserialize_with_set_datetimes(self):
        """Test task deserialization parses datetime strings."""
        serialized = {
            "user_id": "1", "beatmapset_id": "2", "queue_id": "3",
            "comment": "test", "mv_checked": "True",
            "completed_at": "2024-06-15T12:00:00+00:00", "failed_at": "",
        }
        restored = QueueRequestHandlerTask.deserialize(serialized)
        assert isinstance(restored.completed_at, datetime)
        assert restored.completed_at.year == 2024
        assert restored.mv_checked is True

    def test_hashed_id_is_deterministic(self):
        """Test hashed_id is deterministic for same inputs."""
        t1 = QueueRequestHandlerTask(user_id=1, beatmapset_id=2, queue_id=3, comment="a", mv_checked=False)
        t2 = QueueRequestHandlerTask(user_id=1, beatmapset_id=2, queue_id=3, comment="b", mv_checked=False)
        assert t1.hashed_id == t2.hashed_id

    def test_hashed_id_is_positive(self):
        """Test hashed_id is always a positive integer."""
        task = QueueRequestHandlerTask(user_id=1, beatmapset_id=2, queue_id=3, comment="a", mv_checked=False)
        assert task.hashed_id > 0
