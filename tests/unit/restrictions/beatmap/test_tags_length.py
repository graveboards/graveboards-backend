import pytest
from unittest.mock import MagicMock

from app.database.restrictions.validators.beatmap.tags import TagsRestriction
from app.database.restrictions.validators.beatmap.length import LengthRestriction
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError


def _make_beatmap(hit_length=180, total_length=200, top_tag_ids=None, version="Normal"):
    bm = MagicMock()
    bm.hit_length = hit_length
    bm.total_length = total_length
    bm.top_tag_ids = top_tag_ids or []
    bm.version = version
    return bm


class TestTagsRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_any_required_tag_present(self):
        validator = TagsRestriction()
        beatmaps = [_make_beatmap(top_tag_ids=[{"tag_id": 1}, {"tag_id": 2}])]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(tags="1,2,3"),
            beatmaps=beatmaps,
            config={"tag_ids": [2, 3], "logic": "any"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_all_required_tags_present(self):
        validator = TagsRestriction()
        beatmaps = [_make_beatmap(top_tag_ids=[{"tag_id": 1}, {"tag_id": 2}, {"tag_id": 3}])]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(tags="1,2,3"),
            beatmaps=beatmaps,
            config={"tag_ids": [1, 2], "logic": "all"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_no_tags_match_any(self):
        validator = TagsRestriction()
        beatmaps = [_make_beatmap(top_tag_ids=[{"tag_id": 4}])]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(tags="4,5"),
            beatmaps=beatmaps,
            config={"tag_ids": [1, 2], "logic": "any"},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fallback_to_beatmapset_tags(self):
        validator = TagsRestriction()
        beatmaps = [_make_beatmap(top_tag_ids=[])]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(tags="1,2,3"),
            beatmaps=beatmaps,
            config={"tag_ids": [2], "logic": "any"},
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_when_no_required_tags(self):
        validator = TagsRestriction()
        beatmaps = [_make_beatmap()]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"tag_ids": [], "logic": "any"},
        )
        await validator.check(context)


class TestLengthRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_all_in_range(self):
        validator = LengthRestriction()
        beatmaps = [_make_beatmap(hit_length=150, total_length=180)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={
                "min_hit_length": 100,
                "max_hit_length": 200,
                "min_total_length": 120,
                "max_total_length": 300,
            },
        )
        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_hit_length_below_min(self):
        validator = LengthRestriction()
        beatmaps = [_make_beatmap(hit_length=50, total_length=180)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"min_hit_length": 100},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_total_length_above_max(self):
        validator = LengthRestriction()
        beatmaps = [_make_beatmap(hit_length=150, total_length=400)]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"max_total_length": 300},
        )

        with pytest.raises(RestrictionViolationError):
            await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_logic_raises_on_specific_beatmap(self):
        validator = LengthRestriction()
        beatmaps = [
            _make_beatmap(hit_length=150, total_length=180, version="Normal"),
            _make_beatmap(hit_length=50, total_length=60, version="Easy"),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={"min_hit_length": 100, "logic": "all"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await validator.check(context)

        assert "Easy" in str(exc_info.value.detail)
