import pytest
from unittest.mock import AsyncMock, MagicMock

from app.database.rules.validators.metadata.song_identity import (
    SongIdentityProvider,
    _normalize_text,
)
from app.database.rules.validators.metadata.beatmap_stats import BeatmapStatsProvider
from app.database.rules.validators.metadata.creator_identity import CreatorIdentityProvider
from app.database.rules.validators.metadata.duration import DurationProvider
from app.database.rules.context import ExecutionContext


def _make_context(beatmapset=None, beatmaps=None):
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=beatmapset,
        beatmaps=beatmaps if beatmaps is not None else [],
    )


def _make_beatmap(difficulty_rating=5.0, ar=5.0, accuracy=10.0, drain=5.0, bpm=150.0, mode="osu", owners=None):
    bm = MagicMock()
    bm.difficulty_rating = difficulty_rating
    bm.ar = ar
    bm.accuracy = accuracy
    bm.drain = drain
    bm.bpm = bpm
    bm.mode = mode
    bm.owners = owners or []
    return bm


class TestNormalizeText:
    @pytest.mark.unit
    def test_strips_tv_size(self):
        result = _normalize_text("Artist - Song (TV Size)")
        assert "TV Size" not in result
        assert "Artist" in result

    @pytest.mark.unit
    def test_strips_extended_ver(self):
        result = _normalize_text("Artist - Song (Extended ver.)")
        assert "Extended" not in result

    @pytest.mark.unit
    def test_strips_remix(self):
        result = _normalize_text("Artist - Song (Remix)")
        assert "Remix" not in result

    @pytest.mark.unit
    def test_strips_radio_edit(self):
        result = _normalize_text("Artist - Song (Radio Edit)")
        assert "Radio" not in result

    @pytest.mark.unit
    def test_strips_instrumental(self):
        result = _normalize_text("Artist - Song (Instrumental)")
        assert "Instrumental" not in result

    @pytest.mark.unit
    def test_strips_punctuation(self):
        result = _normalize_text("Artist - Song (feat. Someone)")
        assert "(" not in result
        assert ")" not in result
        assert "." not in result

    @pytest.mark.unit
    def test_collapses_whitespace(self):
        result = _normalize_text("Artist   -   Song")
        assert "  " not in result

    @pytest.mark.unit
    def test_plain_text_unchanged(self):
        result = _normalize_text("Artist - Song")
        assert result == "Artist - Song"


class TestSongIdentityProvider:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resolves_identity(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Test Artist",
            artist_unicode="Test Artist",
            title="Test Song",
            title_unicode="Test Song",
            bpm=150.0,
        )
        context = _make_context(beatmapset=beatmapset)
        result = await provider.resolve(context)

        assert result["artist"] == "Test Artist"
        assert result["title"] == "Test Song"
        assert result["normalized_artist"] == "Test Artist"
        assert result["normalized_title"] == "Test Song"
        assert result["duration"] == 150.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normalizes_version_markers(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song (TV Size)",
            title_unicode="Song (TV Size)",
            bpm=150.0,
        )
        context = _make_context(beatmapset=beatmapset)
        result = await provider.resolve(context)

        assert "(TV Size)" not in result["normalized_title"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_beatmapset(self):
        provider = SongIdentityProvider()
        context = _make_context(beatmapset=None)
        result = await provider.resolve(context)

        assert result["artist"] == ""
        assert result["title"] == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_beatmapset_with_empty_fields(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock()
        beatmapset.artist = ""
        beatmapset.artist_unicode = ""
        beatmapset.title = ""
        beatmapset.title_unicode = ""
        beatmapset.bpm = 0
        context = _make_context(beatmapset=beatmapset)
        result = await provider.resolve(context)

        assert result["normalized_artist"] == ""
        assert result["normalized_title"] == ""


class TestBeatmapStatsProvider:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_computes_aggregate_stats(self):
        provider = BeatmapStatsProvider()
        beatmaps = [
            _make_beatmap(difficulty_rating=4.0, ar=4.0, bpm=140.0),
            _make_beatmap(difficulty_rating=6.0, ar=6.0, bpm=160.0),
        ]
        context = _make_context(beatmaps=beatmaps)
        result = await provider.resolve(context)

        assert result["min_sr"] == 4.0
        assert result["max_sr"] == 6.0
        assert result["avg_sr"] == 5.0
        assert result["min_ar"] == 4.0
        assert result["max_ar"] == 6.0
        assert result["difficulty_count"] == 2
        assert "osu" in result["modes"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_beatmaps(self):
        provider = BeatmapStatsProvider()
        context = _make_context()
        result = await provider.resolve(context)

        assert result["min_sr"] == 0.0
        assert result["difficulty_count"] == 0


class TestCreatorIdentityProvider:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resolves_creator(self):
        provider = CreatorIdentityProvider()
        beatmapset = MagicMock(user_id=111, creator="MainCreator")
        beatmaps = [
            _make_beatmap(owners=[{"id": 222, "username": "Mapper1"}]),
            _make_beatmap(owners=[{"id": 222, "username": "Mapper1"}]),
            _make_beatmap(owners=[{"id": 333, "username": "Mapper2"}]),
        ]
        context = _make_context(beatmapset=beatmapset, beatmaps=beatmaps)
        result = await provider.resolve(context)

        assert result["artist_creator_id"] == 111
        assert result["artist_creator_username"] == "MainCreator"
        assert 222 in result["mapper_ids"]
        assert 333 in result["mapper_ids"]
        assert len(result["mapper_ids"]) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_no_owners(self):
        provider = CreatorIdentityProvider()
        beatmapset = MagicMock(user_id=111, creator="MainCreator")
        beatmaps = [_make_beatmap(owners=[])]
        context = _make_context(beatmapset=beatmapset, beatmaps=beatmaps)
        result = await provider.resolve(context)

        assert result["mapper_ids"] == []


class TestDurationProvider:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resolves_duration(self):
        provider = DurationProvider()
        beatmapset = MagicMock(bpm=150.0, title="Song", title_unicode="Song")
        beatmaps = [_make_beatmap(), _make_beatmap()]
        beatmaps[0].total_length = 180
        beatmaps[1].total_length = 200
        context = _make_context(beatmapset=beatmapset, beatmaps=beatmaps)
        result = await provider.resolve(context)

        assert result["original_duration"] == 150.0
        assert result["normalized_duration"] == 200
        assert result["has_version_marker"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detects_version_marker(self):
        provider = DurationProvider()
        beatmapset = MagicMock(bpm=150.0, title="Song (TV Size)", title_unicode="Song (TV Size)")
        context = _make_context(beatmapset=beatmapset, beatmaps=[])
        result = await provider.resolve(context)

        assert result["has_version_marker"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_original_duration_when_no_beatmaps(self):
        provider = DurationProvider()
        beatmapset = MagicMock(bpm=150.0, title="Song", title_unicode="Song")
        context = _make_context(beatmapset=beatmapset, beatmaps=[])
        result = await provider.resolve(context)

        assert result["normalized_duration"] == 150.0
