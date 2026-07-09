import pytest

from app.database.restrictions.validators.metadata.song_identity import (
    _normalize_text,
    SongIdentityProvider,
)
from app.database.restrictions.context import ExecutionContext
from unittest.mock import AsyncMock, MagicMock


class TestNormalizeTextComprehensive:
    @pytest.mark.unit
    def test_tv_size(self):
        result = _normalize_text("Artist - Song (TV Size)")
        assert "TV Size" not in result
        assert "Artist" in result
        assert "Song" in result

    @pytest.mark.unit
    def test_extended_ver_with_period(self):
        result = _normalize_text("Artist - Song (Extended ver.)")
        assert "Extended" not in result
        assert "Artist" in result
        assert "Song" in result

    @pytest.mark.unit
    def test_extended_ver_without_period(self):
        result = _normalize_text("Artist - Song (Extended ver)")
        assert "Extended" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_remix(self):
        result = _normalize_text("Artist - Song (Remix)")
        assert "Remix" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_radio_edit(self):
        result = _normalize_text("Artist - Song (Radio Edit)")
        assert "Radio" not in result
        assert "Edit" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_album_edit(self):
        result = _normalize_text("Artist - Song (Album Edit)")
        assert "Album" not in result
        assert "Edit" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_full_ver(self):
        result = _normalize_text("Artist - Song (Full ver.)")
        assert "Full" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_instrumental(self):
        result = _normalize_text("Artist - Song (Instrumental)")
        assert "Instrumental" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_single_version(self):
        result = _normalize_text("Artist - Song (Single Version)")
        assert "Single" not in result
        assert "Version" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_radio_version(self):
        result = _normalize_text("Artist - Song (Radio Version)")
        assert "Radio" not in result
        assert "Version" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_nightcore_ver(self):
        result = _normalize_text("Artist - Song (Nightcore Ver.)")
        assert "Nightcore" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_cut_version(self):
        result = _normalize_text("Artist - Song (Cut version)")
        assert "Cut" not in result
        assert "version" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_club_mix(self):
        result = _normalize_text("Artist - Song (Club Mix)")
        assert "Club" not in result
        assert "Mix" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_dub_mix(self):
        result = _normalize_text("Artist - Song (Dub Mix)")
        assert "Dub" not in result
        assert "Mix" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_acoustic_version(self):
        result = _normalize_text("Artist - Song (Acoustic Version)")
        assert "Acoustic" not in result
        assert "Version" not in result
        assert "Song" in result

    @pytest.mark.unit
    def test_live_version(self):
        result = _normalize_text("Artist - Song (Live Version)")
        assert "Live" not in result
        assert "Version" not in result
        assert "Song" in result

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
        assert result == "Artist - Song"

    @pytest.mark.unit
    def test_plain_text_unchanged(self):
        result = _normalize_text("Artist - Song")
        assert result == "Artist - Song"

    @pytest.mark.unit
    def test_bilingual_artist(self):
        result = _normalize_text("Artist_unicode - Song_unicode")
        assert result == "Artist_unicode - Song_unicode"

    @pytest.mark.unit
    def test_combined_normalization(self):
        result = _normalize_text("Artist - Song (TV Size) (feat. Someone)")
        assert "Artist" in result
        assert "Song" in result

    @pytest.mark.unit
    def test_case_insensitive_matching(self):
        result = _normalize_text("Artist - Song (tv size)")
        assert "tv" not in result
        assert "size" not in result
        assert "Song" in result


class TestSongIdentityProviderComprehensive:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normalizes_tv_size_title(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song (TV Size)",
            title_unicode="Song (TV Size)",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert "(TV Size)" not in result["normalized_title"]
        assert result["normalized_title"] == "Song"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normalizes_extended_ver_title(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song (Extended ver.)",
            title_unicode="Song (Extended ver.)",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert "Extended" not in result["normalized_title"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normalizes_remix_title(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song (Remix)",
            title_unicode="Song (Remix)",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert "Remix" not in result["normalized_title"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normalizes_radio_edit_title(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song (Radio Edit)",
            title_unicode="Song (Radio Edit)",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert "Radio" not in result["normalized_title"]
        assert "Edit" not in result["normalized_title"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_plain_title_unchanged(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song",
            title_unicode="Song",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert result["normalized_title"] == "Song"
        assert result["normalized_artist"] == "Artist"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bilingual_matching(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Romaji Artist",
            artist_unicode="Unicode Artist",
            title="Romaji Title",
            title_unicode="Unicode Title",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert result["normalized_artist"] == "Romaji Artist"
        assert result["normalized_title"] == "Romaji Title"
        assert result["normalized_artist_unicode"] == "Unicode Artist"
        assert result["normalized_title_unicode"] == "Unicode Title"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_strips_punctuation_from_title(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock(
            artist="Artist",
            artist_unicode="Artist",
            title="Song (feat. Someone)",
            title_unicode="Song (feat. Someone)",
            bpm=150.0,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert "(" not in result["normalized_title"]
        assert ")" not in result["normalized_title"]
        assert "." not in result["normalized_title"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_beatmapset(self):
        provider = SongIdentityProvider()
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=None,
        )
        result = await provider.resolve(context)

        assert result["artist"] == ""
        assert result["title"] == ""
        assert result["normalized_artist"] == ""
        assert result["normalized_title"] == ""
        assert result["duration"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_missing_bpm_attribute(self):
        provider = SongIdentityProvider()
        beatmapset = MagicMock()
        beatmapset.artist = "Artist"
        beatmapset.artist_unicode = "Artist"
        beatmapset.title = "Song"
        beatmapset.title_unicode = "Song"
        del beatmapset.bpm

        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
        )
        result = await provider.resolve(context)

        assert result["duration"] == 0
