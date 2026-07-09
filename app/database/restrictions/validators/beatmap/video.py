from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import VideoConfig


class VideoRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_video"
    config_schema = VideoConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        beatmapset = context.beatmapset

        if beatmapset is None:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset metadata not available",
            )

        has_video = beatmapset.video
        allowed = config.get("allowed", True)

        if allowed and not has_video:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset does not have a video but one is required",
            )
        if not allowed and has_video:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset has a video but videos are not allowed",
            )
