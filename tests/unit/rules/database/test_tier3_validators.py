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


def _make_context(beatmapset=None, osu_client=None, session=None):
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=beatmapset,
        osu_client=osu_client,
        db=AsyncMock(),
        redis=AsyncMock(),
        session=session,
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


def _make_mock_osu_client_pageable(initial_results=None, subsequent_results=None):
    """Create a mock osu client where search_beatmapsets returns different results per call."""
    client = AsyncMock()
    call_count = [0]

    async def searchable(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return initial_results or {"beatmapsets": []}
        return subsequent_results or {"beatmapsets": []}

    client.search_beatmapsets = AsyncMock(side_effect=searchable)
    return client

def _make_session(rows):
    """Mock an AsyncSession whose execute(...).all() yields the given rows.

    Each row is (artist, title, artist_unicode, title_unicode, beatmapset_id).
    """
    session = AsyncMock()
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)
    return session


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
        osu_client = _make_mock_osu_client_pageable(
            initial_results={
                "beatmapsets": [],
            },
            subsequent_results={"beatmapsets": []},
        )
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
        assert kwargs["mode"] == 1

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
    def test_defaults(self):
        config = UniqueArtistTitleConfig()
        assert config.normalize_versions is True


def _unique_context(session):
    beatmapset = MagicMock()
    beatmapset.id = 999
    beatmapset.artist = "Test Artist"
    beatmapset.artist_unicode = "Test Artist"
    beatmapset.title = "Test Song"
    beatmapset.title_unicode = "Test Song"
    beatmapset.bpm = 150.0
    context = _make_context(beatmapset=beatmapset, session=session, osu_client=AsyncMock())
    context.config = {"normalize_versions": True}
    return context


_UNIQUE_IDENTITY = {
    "artist": "Test Artist",
    "title": "Test Song",
    "artist_unicode": "Test Artist",
    "title_unicode": "Test Song",
    "normalized_artist": "test artist",
    "normalized_title": "test song",
}


class TestUniqueArtistTitleRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_duplicate(self):
        rule = UniqueArtistTitleRestriction()
        session = _make_session([
            ("Other Artist", "Other Song", "Other Artist", "Other Song", 111),
        ])
        context = _unique_context(session)

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value=dict(_UNIQUE_IDENTITY))
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_duplicate_found(self):
        rule = UniqueArtistTitleRestriction()
        session = _make_session([
            ("Test Artist", "Test Song", "Test Artist", "Test Song", 12345),
        ])
        context = _unique_context(session)

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value=dict(_UNIQUE_IDENTITY))
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with pytest.raises(RuleViolationError, match="already has a request in this queue"):
            with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
                await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_excludes_current_beatmapset(self):
        # A duplicate row that IS the submitted beatmapset must not trip the rule.
        rule = UniqueArtistTitleRestriction()
        session = _make_session([
            ("Test Artist", "Test Song", "Test Artist", "Test Song", 999),
        ])
        context = _unique_context(session)

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value=dict(_UNIQUE_IDENTITY))
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_empty_queue(self):
        rule = UniqueArtistTitleRestriction()
        session = _make_session([])
        context = _unique_context(session)

        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value=dict(_UNIQUE_IDENTITY))
        context.metadata_providers = {"song_identity": lambda: mock_provider}

        with patch.object(ExecutionContext, "get_metadata", new=mock_provider.resolve):
            await rule.check(context)
