from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import DifficultyCountConfig


class DifficultyCountRestriction(BeatmapRestrictionBase):
    type = "beatmap_difficulty_count"
    config_schema = DifficultyCountConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        beatmaps = context.beatmaps or []
        count = len(beatmaps)

        min_count = config.get("min")
        max_count = config.get("max")

        if min_count is not None and count < min_count:
            raise RuleViolationError(
                self.type,
                f"Beatmapset has {count} difficulty/difficulties, minimum "
                f"required is {min_count}",
            )
        if max_count is not None and count > max_count:
            raise RuleViolationError(
                self.type,
                f"Beatmapset has {count} difficulty/difficulties, maximum "
                f"allowed is {max_count}",
            )
