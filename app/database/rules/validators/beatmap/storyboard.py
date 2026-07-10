from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import StoryboardConfig


class StoryboardRestriction(BeatmapRestrictionBase):
    type = "beatmap_storyboard"
    config_schema = StoryboardConfig

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

        if allowed and not has_storyboard:
            raise RuleViolationError(
                self.type,
                "Beatmapset does not have a storyboard but one is required",
            )
        if not allowed and has_storyboard:
            raise RuleViolationError(
                self.type,
                "Beatmapset has a storyboard but storyboards are not allowed",
            )
