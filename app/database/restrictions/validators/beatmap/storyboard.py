from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import StoryboardConfig


class StoryboardRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_storyboard"
    config_schema = StoryboardConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        beatmapset = context.beatmapset

        if beatmapset is None:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset metadata not available",
            )

        has_storyboard = beatmapset.storyboard
        allowed = config.get("allowed", True)

        if allowed and not has_storyboard:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset does not have a storyboard but one is required",
            )
        if not allowed and has_storyboard:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset has a storyboard but storyboards are not allowed",
            )
