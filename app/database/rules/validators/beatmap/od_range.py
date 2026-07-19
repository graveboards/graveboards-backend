from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import ODRangeConfig


class ODRangeRestriction(BeatmapRestrictionBase):
    type = "beatmap_od_range"
    config_schema = ODRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        od_values = [b.accuracy for b in beatmaps]
        min_od = config.get("min")
        max_od = config.get("max")

        if logic == "all":
            for beatmap, od in zip(beatmaps, od_values):
                if min_od is not None and od < min_od:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' OD ({od:.2f}) is below "
                        f"minimum allowed OD ({min_od:.2f})",
                    )
                if max_od is not None and od > max_od:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' OD ({od:.2f}) exceeds "
                        f"maximum allowed OD ({max_od:.2f})",
                    )
        else:
            # logic == "any": at least one beatmap must fall within the range.
            matched = any(
                (min_od is None or od >= min_od) and (max_od is None or od <= max_od)
                for od in od_values
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has OD within the allowed range "
                    f"(min={min_od}, max={max_od}). "
                    f"Values: {[round(v, 2) for v in od_values]}",
                )
