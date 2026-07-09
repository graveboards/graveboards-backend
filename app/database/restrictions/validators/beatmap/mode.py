from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import ModeConfig


class ModeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_mode"
    config_schema = ModeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        allowed_modes = set(config.get("allowed_modes", []))
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RestrictionViolationError(
                self.restriction_type,
                "No beatmaps available in beatmapset",
            )

        actual_modes = {b.mode for b in beatmaps}
        unsupported = actual_modes - allowed_modes

        if unsupported:
            raise RestrictionViolationError(
                self.restriction_type,
                f"Beatmapset contains unsupported game modes: {unsupported}. "
                f"Allowed modes: {allowed_modes}",
            )
