from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import DurationConfig


class DurationRestriction(BeatmapRestrictionBase):
    type = "beatmap_duration"
    config_schema = DurationConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "max")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        if logic == "max":
            max_length = max(b.total_length for b in beatmaps)
            min_seconds = config.get("min_seconds")
            max_seconds = config.get("max_seconds")
            if min_seconds is not None and max_length < min_seconds:
                raise RuleViolationError(
                    self.type,
                    f"Longest beatmap duration ({max_length}s) is below minimum "
                    f"allowed duration ({min_seconds}s)",
                )
            if max_seconds is not None and max_length > max_seconds:
                raise RuleViolationError(
                    self.type,
                    f"Longest beatmap duration ({max_length}s) exceeds maximum "
                    f"allowed duration ({max_seconds}s)",
                )

        elif logic == "min":
            min_length = min(b.total_length for b in beatmaps)
            min_seconds = config.get("min_seconds")
            max_seconds = config.get("max_seconds")
            if min_seconds is not None and min_length < min_seconds:
                raise RuleViolationError(
                    self.type,
                    f"Shortest beatmap duration ({min_length}s) is below minimum "
                    f"allowed duration ({min_seconds}s)",
                )
            if max_seconds is not None and min_length > max_seconds:
                raise RuleViolationError(
                    self.type,
                    f"Shortest beatmap duration ({min_length}s) exceeds maximum "
                    f"allowed duration ({max_seconds}s)",
                )

        elif logic == "all":
            min_seconds = config.get("min_seconds", 0)
            max_seconds = config.get("max_seconds")
            for beatmap in beatmaps:
                if beatmap.total_length < min_seconds:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' duration "
                        f"({beatmap.total_length}s) is below minimum "
                        f"allowed duration ({min_seconds}s)",
                    )
                if max_seconds is not None and beatmap.total_length > max_seconds:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' duration "
                        f"({beatmap.total_length}s) exceeds maximum "
                        f"allowed duration ({max_seconds}s)",
                    )
