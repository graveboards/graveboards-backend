from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import CSRangeConfig


class CSRangeRestriction(BeatmapRestrictionBase):
    type = "beatmap_cs_range"
    config_schema = CSRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        cs_values = [b.cs for b in beatmaps]
        min_cs = config.get("min")
        max_cs = config.get("max")

        if logic == "all":
            for beatmap, cs in zip(beatmaps, cs_values):
                if min_cs is not None and cs < min_cs:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' CS ({cs:.2f}) is below "
                        f"minimum allowed CS ({min_cs:.2f})",
                    )
                if max_cs is not None and cs > max_cs:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' CS ({cs:.2f}) exceeds "
                        f"maximum allowed CS ({max_cs:.2f})",
                    )
        else:
            # logic == "any": at least one beatmap must fall within the range.
            matched = any(
                (min_cs is None or cs >= min_cs) and (max_cs is None or cs <= max_cs)
                for cs in cs_values
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has CS within the allowed range "
                    f"(min={min_cs}, max={max_cs}). "
                    f"Values: {[round(v, 2) for v in cs_values]}",
                )
