import pytest
from unittest.mock import MagicMock

from app.database.rules.validators.beatmap.ar_range import ARRangeRestriction
from app.database.rules.validators.beatmap.od_range import ODRangeRestriction
from app.database.rules.validators.beatmap.hp_range import HPRangeRestriction
from app.database.rules.validators.beatmap.cs_range import CSRangeRestriction
from app.database.rules.validators.beatmap.drain_range import DrainRangeRestriction
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError


def _make_beatmap(ar=5.0, accuracy=10.0, drain=5.0, cs=4.0, version="Normal"):
    bm = MagicMock()
    bm.ar = ar
    bm.accuracy = accuracy
    bm.drain = drain
    bm.cs = cs
    bm.version = version
    return bm


def _make_context(beatmaps=None, config=None, type="beatmap_ar_range"):
    ctx = ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=MagicMock(),
        beatmaps=beatmaps or [],
        config=config or {},
    )
    return ctx


class TestARRangeRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_in_range(self):
        validator = ARRangeRestriction()
        beatmaps = [_make_beatmap(ar=5.0), _make_beatmap(ar=6.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 4.0, "max": 7.0},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_below_min(self):
        validator = ARRangeRestriction()
        beatmaps = [_make_beatmap(ar=3.0), _make_beatmap(ar=6.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 4.0},
        )

        with pytest.raises(RuleViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_above_max(self):
        validator = ARRangeRestriction()
        beatmaps = [_make_beatmap(ar=6.0), _make_beatmap(ar=8.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 7.0},
        )

        with pytest.raises(RuleViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_raises_on_specific_beatmap(self):
        validator = ARRangeRestriction()
        beatmaps = [_make_beatmap(ar=5.0, version="Normal"), _make_beatmap(ar=8.0, version="Insane")]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 7.0, "logic": "all"},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await validator.check(context)

        assert "Insane" in str(exc_info.value.detail)


class TestODRangeRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_in_range(self):
        validator = ODRangeRestriction()
        beatmaps = [_make_beatmap(accuracy=9.0), _make_beatmap(accuracy=10.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 8.0, "max": 11.0},
            type="beatmap_od_range",
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_below_min(self):
        validator = ODRangeRestriction()
        beatmaps = [_make_beatmap(accuracy=7.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 8.0},
            type="beatmap_od_range",
        )

        with pytest.raises(RuleViolationError):
            await validator.check(context)


class TestHPRangeRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_in_range(self):
        validator = HPRangeRestriction()
        beatmaps = [_make_beatmap(drain=4.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0, "max": 5.0},
            type="beatmap_hp_range",
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_above_max(self):
        validator = HPRangeRestriction()
        beatmaps = [_make_beatmap(drain=6.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 5.0},
            type="beatmap_hp_range",
        )

        with pytest.raises(RuleViolationError):
            await validator.check(context)


class TestCSRangeRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_in_range(self):
        validator = CSRangeRestriction()
        beatmaps = [_make_beatmap(cs=3.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 2.0, "max": 4.0},
            type="beatmap_cs_range",
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_outside_range(self):
        validator = CSRangeRestriction()
        beatmaps = [_make_beatmap(cs=5.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"max": 4.0},
            type="beatmap_cs_range",
        )

        with pytest.raises(RuleViolationError):
            await validator.check(context)


class TestDrainRangeRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_in_range(self):
        validator = DrainRangeRestriction()
        beatmaps = [_make_beatmap(drain=4.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0, "max": 5.0},
            type="beatmap_drain_range",
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_below_min(self):
        validator = DrainRangeRestriction()
        beatmaps = [_make_beatmap(drain=1.0)]
        context = _make_context(
            beatmaps=beatmaps,
            config={"min": 3.0},
            type="beatmap_drain_range",
        )

        with pytest.raises(RuleViolationError):
            await validator.check(context)
