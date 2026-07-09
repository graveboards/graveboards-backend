from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import ARRangeConfig


class ARRangeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_ar_range"
    config_schema = ARRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RestrictionViolationError(
                self.restriction_type,
                "No beatmaps available in beatmapset",
            )

        ar_values = [b.ar for b in beatmaps]
        min_ar = config.get("min")
        max_ar = config.get("max")

        if logic == "all":
            for beatmap, ar in zip(beatmaps, ar_values):
                if min_ar is not None and ar < min_ar:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' AR ({ar:.2f}) is below "
                        f"minimum allowed AR ({min_ar:.2f})",
                    )
                if max_ar is not None and ar > max_ar:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' AR ({ar:.2f}) exceeds "
                        f"maximum allowed AR ({max_ar:.2f})",
                    )
        else:
            if min_ar is not None and min(ar_values) < min_ar:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have AR below minimum allowed "
                    f"({min_ar:.2f}). Lowest: {min(ar_values):.2f}",
                )
            if max_ar is not None and max(ar_values) > max_ar:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have AR above maximum allowed "
                    f"({max_ar:.2f}). Highest: {max(ar_values):.2f}",
                )
