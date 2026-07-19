from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import DrainRangeConfig


class DrainRangeRestriction(BeatmapRestrictionBase):
    type = "beatmap_drain_range"
    config_schema = DrainRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        drain_values = [b.hit_length for b in beatmaps]
        min_drain = config.get("min")
        max_drain = config.get("max")

        if logic == "all":
            for beatmap, drain in zip(beatmaps, drain_values):
                if min_drain is not None and drain < min_drain:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' drain time ({drain}s) "
                        f"is below minimum allowed ({min_drain}s)",
                    )
                if max_drain is not None and drain > max_drain:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' drain time ({drain}s) "
                        f"exceeds maximum allowed ({max_drain}s)",
                    )
        else:
            # logic == "any": at least one beatmap must fall within the range.
            matched = any(
                (min_drain is None or drain >= min_drain)
                and (max_drain is None or drain <= max_drain)
                for drain in drain_values
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has drain time within the allowed range "
                    f"(min={min_drain}, max={max_drain}). "
                    f"Values: {drain_values}",
                )
