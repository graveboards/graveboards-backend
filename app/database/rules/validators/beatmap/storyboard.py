"""Storyboard restriction for ranked-beatmap submission."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import StoryboardConfig

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext


class StoryboardRestriction(BeatmapRestrictionBase):
    """Require the beatmapset to either include or exclude a storyboard."""

    type = "beatmap_storyboard"
    config_schema = StoryboardConfig

    @override
    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        beatmapset = context.beatmapset

        if beatmapset is None:
            raise RuleViolationError(
                self.type,
                "Beatmapset metadata not available",
            )

        has_storyboard = beatmapset.storyboard
        allowed = config.get("allowed", True)

        if not allowed and has_storyboard:
            raise RuleViolationError(
                self.type,
                "Beatmapset has a storyboard but storyboards are not allowed",
            )
