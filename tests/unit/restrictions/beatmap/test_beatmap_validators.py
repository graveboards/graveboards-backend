import pytest
from unittest.mock import MagicMock

from app.database.restrictions.validators.beatmap.bpm import BPMRestriction
from app.database.restrictions.validators.beatmap.genre import GenreRestriction
from app.database.restrictions.validators.beatmap.language import LanguageRestriction
from app.database.restrictions.validators.beatmap.mode import ModeRestriction
from app.database.restrictions.validators.beatmap.difficulty_count import DifficultyCountRestriction
from app.database.restrictions.validators.beatmap.storyboard import StoryboardRestriction
from app.database.restrictions.validators.beatmap.video import VideoRestriction
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError


def _make_beatmap(bpm=150.0, mode="osu", version="Normal"):
    bm = MagicMock()
    bm.bpm = bpm
    bm.mode = mode
    bm.version = version
    bm.top_tag_ids = []
    bm.hit_length = 180
    bm.total_length = 200
    return bm


def _make_genre(id: int, name: str):
    g = MagicMock()
    g.id = id
    g.name = name
    return g


def _make_language(id: int, name: str):
    l = MagicMock()
    l.id = id
    l.name = name
    return l


class TestBPMRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_in_range(self):
        validator = BPMRestriction()
        beatmaps = [_make_beatmap(bpm=140.0), _make_beatmap(bpm=160.0)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(bpm=150.0),
            beatmaps=beatmaps,
            config={"min_bpm": 100.0, "max_bpm": 200.0},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_below_min(self):
        validator = BPMRestriction()
        beatmaps = [_make_beatmap(bpm=50.0)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(bpm=50.0),
            beatmaps=beatmaps,
            config={"min_bpm": 100.0},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_avg_logic_passes(self):
        validator = BPMRestriction()
        beatmaps = [_make_beatmap(bpm=140.0), _make_beatmap(bpm=160.0)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(bpm=150.0),
            beatmaps=beatmaps,
            config={"min_bpm": 100.0, "max_bpm": 200.0, "logic": "avg"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_raises_on_specific_beatmap(self):
        validator = BPMRestriction()
        beatmaps = [_make_beatmap(bpm=140.0, version="Normal"), _make_beatmap(bpm=300.0, version="Insane")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(bpm=150.0),
            beatmaps=beatmaps,
            config={"max_bpm": 200.0, "logic": "all"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "Insane" in str(exc_info.value.detail)


class TestGenreRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_genre_matches(self):
        validator = GenreRestriction()
        genre = _make_genre(2, "Video Game")
        beatmapset = MagicMock(genre=genre)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"genre_ids": [2, 3], "logic": "any"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_genre_not_in_list(self):
        validator = GenreRestriction()
        genre = _make_genre(5, "Pop")
        beatmapset = MagicMock(genre=genre)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"genre_ids": [2, 3], "logic": "any"},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_genre_is_none(self):
        validator = GenreRestriction()
        beatmapset = MagicMock(genre=None)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"genre_ids": [2]},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)


class TestLanguageRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_language_matches(self):
        validator = LanguageRestriction()
        lang = _make_language(2, "English")
        beatmapset = MagicMock(language=lang)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"language_ids": [2, 3], "logic": "any"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_language_not_in_list(self):
        validator = LanguageRestriction()
        lang = _make_language(4, "Chinese")
        beatmapset = MagicMock(language=lang)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"language_ids": [2, 3], "logic": "any"},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)


class TestModeRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_modes_allowed(self):
        validator = ModeRestriction()
        beatmaps = [_make_beatmap(mode="osu"), _make_beatmap(mode="osu")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"allowed_modes": ["osu"]},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_unsupported_mode(self):
        validator = ModeRestriction()
        beatmaps = [_make_beatmap(mode="osu"), _make_beatmap(mode="taiko")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"allowed_modes": ["osu"]},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "taiko" in str(exc_info.value.detail)


class TestDifficultyCountRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_count_in_range(self):
        validator = DifficultyCountRestriction()
        beatmaps = [_make_beatmap(), _make_beatmap(), _make_beatmap()]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"min": 2, "max": 5},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_too_few(self):
        validator = DifficultyCountRestriction()
        beatmaps = [_make_beatmap()]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"min": 2},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_too_many(self):
        validator = DifficultyCountRestriction()
        beatmaps = [_make_beatmap() for _ in range(6)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"max": 5},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)


class TestStoryboardRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_storyboard_present_and_required(self):
        validator = StoryboardRestriction()
        beatmapset = MagicMock(storyboard=True)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"allowed": True},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_storyboard_required_but_missing(self):
        validator = StoryboardRestriction()
        beatmapset = MagicMock(storyboard=False)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"allowed": True},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_storyboard_present_but_disallowed(self):
        validator = StoryboardRestriction()
        beatmapset = MagicMock(storyboard=True)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"allowed": False},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)


class TestVideoRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_video_present_and_required(self):
        validator = VideoRestriction()
        beatmapset = MagicMock(video=True)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"allowed": True},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_video_required_but_missing(self):
        validator = VideoRestriction()
        beatmapset = MagicMock(video=False)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"allowed": True},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_video_present_but_disallowed(self):
        validator = VideoRestriction()
        beatmapset = MagicMock(video=True)
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=beatmapset,
            beatmaps=[],
            config={"allowed": False},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)
