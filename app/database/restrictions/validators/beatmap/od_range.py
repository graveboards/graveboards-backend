from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import ODRangeConfig


class ODRangeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_od_range"
    config_schema = ODRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RestrictionViolationError(
                self.restriction_type,
                "No beatmaps available in beatmapset",
            )

        od_values = [b.accuracy for b in beatmaps]
        min_od = config.get("min")
        max_od = config.get("max")

        if logic == "all":
            for beatmap, od in zip(beatmaps, od_values):
                if min_od is not None and od < min_od:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' OD ({od:.2f}) is below "
                        f"minimum allowed OD ({min_od:.2f})",
                    )
                if max_od is not None and od > max_od:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' OD ({od:.2f}) exceeds "
                        f"maximum allowed OD ({max_od:.2f})",
                    )
        else:
            if min_od is not None and min(od_values) < min_od:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have OD below minimum allowed "
                    f"({min_od:.2f}). Lowest: {min(od_values):.2f}",
                )
            if max_od is not None and max(od_values) > max_od:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have OD above maximum allowed "
                    f"({max_od:.2f}). Highest: {max(od_values):.2f}",
                )
