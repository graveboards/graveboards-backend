import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.rules.validators.database.never_ranked import (
    NeverRankedRestriction,
    NeverRankedConfig,
)
from app.database.rules.validators.database.unique_artist_title import (
    UniqueArtistTitleRestriction,
    UniqueArtistTitleConfig,
)
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError


def _make_context(beatmapset=None, osu_client=None):
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=beatmapset,
        osu_client=osu_client,
        db=AsyncMock(),
        redis=AsyncMock(),
        metadata_providers={
            "song_identity": MagicMock(),
        },
    )


def _make_mock_osu_client(search_results=None):
    client = AsyncMock()
    client.search_beatmapsets = AsyncMock(
        return_value=search_results or {"beatmapsets": []}
    )
    return client


class TestNeverRankedConfig:
    @pytest.mark.unit
    def test_default_ruleset(self):
        config = NeverRankedConfig()
        assert config.ruleset == "osu"
        assert config.normalize_versions is True

    @pytest.mark.unit
    def test_valid_rulesets(self):
        for ruleset in ["osu", "taiko", "fruits", "mania"]:
            config = NeverRankedConfig(ruleset=ruleset)
            assert config.ruleset == ruleset

    @pytest.mark.unit
    def test_invalid_ruleset(self):
        with pytest.raises(Exception):
            NeverRankedConfig(ruleset="invalid")


class TestNeverRankedRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_ranked_matches(self):
        rule = NeverRankedRestriction()
        osu_client = _make_mock_osu_client({
            "beatmapsets": [
                {"artist": "Different Artist", "title": "Different Song"},
            ]
        })
        beatmapset = MagicMock()
        beatmapset.artist = "Test Artist"
        beatmapset.artist_unicode = "Test Artist"
        beatmapset.title = "Test Song"
        beatmapset.title_unicode = "Test Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Test Artist",
            "artist_unicode": "Test Artist",
            "title": "Test Song",
            "title_unicode": "Test Song",
            "normalized_artist": "Test Artist",
            "normalized_title": "Test Song",
            "normalized_artist_unicode": "Test Artist",
            "normalized_title_unicode": "Test Song",
            "duration": 150.0,
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)

        osu_client.search_beatmapsets.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_ranked_match_found(self):
        rule = NeverRankedRestriction()
        osu_client = _make_mock_osu_client({
            "beatmapsets": [
                {"artist": "Test Artist", "title": "Test Song"},
            ]
        })
        beatmapset = MagicMock()
        beatmapset.artist = "Test Artist"
        beatmapset.artist_unicode = "Test Artist"
        beatmapset.title = "Test Song"
        beatmapset.title_unicode = "Test Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Test Artist",
            "title": "Test Song",
            "normalized_artist": "Test Artist",
            "normalized_title": "Test Song",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with pytest.raises(RuleViolationError, match="already ranked"):
            with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
                await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_normalizes_version_markers_in_search(self):
        rule = NeverRankedRestriction()
        osu_client = _make_mock_osu_client({
            "beatmapsets": [
                {"artist": "Test Artist", "title": "Test Song (TV Size)"},
            ]
        })
        beatmapset = MagicMock()
        beatmapset.artist = "Test Artist"
        beatmapset.artist_unicode = "Test Artist"
        beatmapset.title = "Test Song"
        beatmapset.title_unicode = "Test Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Test Artist",
            "title": "Test Song",
            "normalized_artist": "Test Artist",
            "normalized_title": "Test Song",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with pytest.raises(RuleViolationError, match="already ranked"):
            with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
                await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_uses_correct_ruleset_mapping(self):
        rule = NeverRankedRestriction()
        osu_client = _make_mock_osu_client({"beatmapsets": []})
        beatmapset = MagicMock()
        beatmapset.artist = "Artist"
        beatmapset.artist_unicode = "Artist"
        beatmapset.title = "Song"
        beatmapset.title_unicode = "Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "taiko", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Artist",
            "title": "Song",
            "normalized_artist": "Artist",
            "normalized_title": "Song",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)

        _, kwargs = osu_client.search_beatmapsets.await_args
        assert kwargs["mode"] == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_on_missing_identity(self):
        rule = NeverRankedRestriction()
        osu_client = AsyncMock()
        beatmapset = MagicMock()
        beatmapset.artist = None
        beatmapset.artist_unicode = None
        beatmapset.title = None
        beatmapset.title_unicode = None
        beatmapset.bpm = 0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "",
            "title": "",
            "normalized_artist": "",
            "normalized_title": "",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with pytest.raises(RuleViolationError, match="Could not resolve"):
            with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
                await rule.check(context)


class TestUniqueArtistTitleConfig:
    @pytest.mark.unit
    def test_default_ruleset(self):
        config = UniqueArtistTitleConfig()
        assert config.ruleset == "osu"
        assert config.normalize_versions is True

    @pytest.mark.unit
    def test_valid_rulesets(self):
        for ruleset in ["osu", "taiko", "fruits", "mania"]:
            config = UniqueArtistTitleConfig(ruleset=ruleset)
            assert config.ruleset == ruleset


class TestUniqueArtistTitleRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_duplicate(self):
        rule = UniqueArtistTitleRestriction()
        osu_client = _make_mock_osu_client({
            "beatmapsets": [
                {"artist": "Other Artist", "title": "Other Song"},
            ]
        })
        beatmapset = MagicMock()
        beatmapset.artist = "Test Artist"
        beatmapset.artist_unicode = "Test Artist"
        beatmapset.title = "Test Song"
        beatmapset.title_unicode = "Test Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Test Artist",
            "title": "Test Song",
            "normalized_artist": "Test Artist",
            "normalized_title": "Test Song",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_duplicate_found(self):
        rule = UniqueArtistTitleRestriction()
        osu_client = _make_mock_osu_client({
            "beatmapsets": [
                {"artist": "Test Artist", "title": "Test Song", "beatmapset_id": 12345},
            ]
        })
        beatmapset = MagicMock()
        beatmapset.artist = "Test Artist"
        beatmapset.artist_unicode = "Test Artist"
        beatmapset.title = "Test Song"
        beatmapset.title_unicode = "Test Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Test Artist",
            "title": "Test Song",
            "normalized_artist": "Test Artist",
            "normalized_title": "Test Song",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with pytest.raises(RuleViolationError, match="already has a ranked request"):
            with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
                await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_empty_search_results(self):
        rule = UniqueArtistTitleRestriction()
        osu_client = _make_mock_osu_client({"beatmapsets": []})
        beatmapset = MagicMock()
        beatmapset.artist = "Test Artist"
        beatmapset.artist_unicode = "Test Artist"
        beatmapset.title = "Test Song"
        beatmapset.title_unicode = "Test Song"
        beatmapset.bpm = 150.0

        context = _make_context(
            beatmapset=beatmapset,
            osu_client=osu_client,
        )
        context.config = {"ruleset": "osu", "normalize_versions": True}

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={
            "artist": "Test Artist",
            "title": "Test Song",
            "normalized_artist": "Test Artist",
            "normalized_title": "Test Song",
        })
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)
