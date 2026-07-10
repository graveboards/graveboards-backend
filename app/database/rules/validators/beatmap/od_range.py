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
            if min_od is not None and min(od_values) < min_od:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have OD below minimum allowed "
                    f"({min_od:.2f}). Lowest: {min(od_values):.2f}",
                )
            if max_od is not None and max(od_values) > max_od:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have OD above maximum allowed "
                    f"({max_od:.2f}). Highest: {max(od_values):.2f}",
                )
