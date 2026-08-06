"""Game-mode restriction for ranked-beatmap submission."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import ModeConfig

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext


class ModeRestriction(BeatmapRestrictionBase):
    """Require every beatmap in the set to use an allowed game mode."""

    type = "beatmap_mode"
    config_schema = ModeConfig

    @override
    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        allowed_modes = set(config.get("allowed_modes", []))
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        actual_modes = {b.mode for b in beatmaps}
        unsupported = actual_modes - allowed_modes

        if unsupported:
            raise RuleViolationError(
                self.type,
                f"Beatmapset contains unsupported game modes: {unsupported}. "
                f"Allowed modes: {allowed_modes}",
            )
