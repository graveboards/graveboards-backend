from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import CSRangeConfig


class CSRangeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_cs_range"
    config_schema = CSRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RestrictionViolationError(
                self.restriction_type,
                "No beatmaps available in beatmapset",
            )

        cs_values = [b.cs for b in beatmaps]
        min_cs = config.get("min")
        max_cs = config.get("max")

        if logic == "all":
            for beatmap, cs in zip(beatmaps, cs_values):
                if min_cs is not None and cs < min_cs:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' CS ({cs:.2f}) is below "
                        f"minimum allowed CS ({min_cs:.2f})",
                    )
                if max_cs is not None and cs > max_cs:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' CS ({cs:.2f}) exceeds "
                        f"maximum allowed CS ({max_cs:.2f})",
                    )
        else:
            if min_cs is not None and min(cs_values) < min_cs:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have CS below minimum allowed "
                    f"({min_cs:.2f}). Lowest: {min(cs_values):.2f}",
                )
            if max_cs is not None and max(cs_values) > max_cs:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have CS above maximum allowed "
                    f"({max_cs:.2f}). Highest: {max(cs_values):.2f}",
                )
