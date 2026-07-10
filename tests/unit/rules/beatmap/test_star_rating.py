import pytest
from unittest.mock import MagicMock

from app.database.rules.validators.beatmap.star_rating import StarRatingRestriction
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import StarRatingConfig


def _make_beatmap(sr: float, version: str = "Normal"):
    bm = MagicMock()
    bm.difficulty_rating = sr
    bm.version = version
    return bm


def _make_context(beatmaps=None, config=None):
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=MagicMock(),
        beatmaps=beatmaps or [],
        config=config or {},
    )


class TestStarRatingRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_any_logic_passes_when_all_in_range(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(4.0), _make_beatmap(5.0), _make_beatmap(6.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0, "max": 7.0, "logic": "any"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_any_logic_raises_when_below_min(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(2.0), _make_beatmap(5.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0, "logic": "any"},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await validator.check(context)

        assert "below minimum" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_any_logic_raises_when_above_max(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(5.0), _make_beatmap(8.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 7.0, "logic": "any"},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await validator.check(context)

        assert "above maximum" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_max_logic_passes(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(4.0), _make_beatmap(6.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 7.0, "logic": "max"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_max_logic_raises(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(4.0), _make_beatmap(8.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 7.0, "logic": "max"},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await validator.check(context)

        assert "exceeds maximum" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_min_logic_raises(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(2.0), _make_beatmap(5.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0, "logic": "min"},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await validator.check(context)

        assert "below minimum" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_passes(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(4.0, "Easy"), _make_beatmap(5.0, "Normal"), _make_beatmap(6.0, "Hard")]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0, "max": 7.0, "logic": "all"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_raises_on_specific_beatmap(self):
        validator = StarRatingRestriction()
        beatmaps = [_make_beatmap(4.0, "Normal"), _make_beatmap(8.0, "Extra")]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 7.0, "logic": "all"},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await validator.check(context)

        assert "Extra" in str(exc_info.value.detail)

    @pytest.mark.unit
    def test_config_schema_is_set(self):
        assert StarRatingRestriction.config_schema is StarRatingConfig

    @pytest.mark.unit
    def test_type(self):
        assert StarRatingRestriction.type == "beatmap_star_rating"
