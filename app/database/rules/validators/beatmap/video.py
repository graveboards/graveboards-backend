from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import VideoConfig


class VideoRestriction(BeatmapRestrictionBase):
    type = "beatmap_video"
    config_schema = VideoConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        beatmapset = context.beatmapset

        if beatmapset is None:
            raise RuleViolationError(
                self.type,
                "Beatmapset metadata not available",
            )

        has_video = beatmapset.video
        allowed = config.get("allowed", True)

        if not allowed and has_video:
            raise RuleViolationError(
                self.type,
                "Beatmapset has a video but videos are not allowed",
            )
