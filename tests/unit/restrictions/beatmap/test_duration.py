import pytest
from unittest.mock import AsyncMock, MagicMock

from app.database.restrictions.validators.beatmap.duration import DurationRestriction
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import DurationConfig


def _make_beatmap(total_length: int, version: str = "Easy"):
    bm = MagicMock()
    bm.total_length = total_length
    bm.version = version
    return bm


def _make_context(beatmaps=None, beatmapset=None, config=None):
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=beatmapset or MagicMock(),
        beatmaps=beatmaps or [],
        config=config or {},
    )


class TestDurationRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_max_not_exceeded(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(150), _make_beatmap(170)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max_seconds": 180, "logic": "max"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_max_exceeded(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(150), _make_beatmap(200)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max_seconds": 180, "logic": "max"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "exceeds maximum" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_min_not_below(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(40), _make_beatmap(50)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min_seconds": 30, "logic": "min"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_min_below(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(20), _make_beatmap(50)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min_seconds": 30, "logic": "min"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "below minimum" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_passes_when_all_within_range(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(100), _make_beatmap(150), _make_beatmap(170)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min_seconds": 30, "max_seconds": 200, "logic": "all"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_raises_on_too_short(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(100, "Normal"), _make_beatmap(20, "Easy")]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min_seconds": 30, "max_seconds": 200, "logic": "all"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "Easy" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_raises_on_too_long(self):
        validator = DurationRestriction()
        beatmaps = [_make_beatmap(100, "Normal"), _make_beatmap(250, "Extra")]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min_seconds": 30, "max_seconds": 200, "logic": "all"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "Extra" in str(exc_info.value.detail)

    @pytest.mark.unit
    def test_config_schema_is_set(self):
        assert DurationRestriction.config_schema is DurationConfig

    @pytest.mark.unit
    def test_restriction_type(self):
        assert DurationRestriction.restriction_type == "beatmap_duration"
