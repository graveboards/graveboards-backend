from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import DrainRangeConfig


class DrainRangeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_drain_range"
    config_schema = DrainRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RestrictionViolationError(
                self.restriction_type,
                "No beatmaps available in beatmapset",
            )

        drain_values = [b.drain for b in beatmaps]
        min_drain = config.get("min")
        max_drain = config.get("max")

        if logic == "all":
            for beatmap, drain in zip(beatmaps, drain_values):
                if min_drain is not None and drain < min_drain:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' drain rate ({drain:.2f}) "
                        f"is below minimum allowed ({min_drain:.2f})",
                    )
                if max_drain is not None and drain > max_drain:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' drain rate ({drain:.2f}) "
                        f"exceeds maximum allowed ({max_drain:.2f})",
                    )
        else:
            if min_drain is not None and min(drain_values) < min_drain:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have drain rate below minimum allowed "
                    f"({min_drain:.2f}). Lowest: {min(drain_values):.2f}",
                )
            if max_drain is not None and max(drain_values) > max_drain:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have drain rate above maximum allowed "
                    f"({max_drain:.2f}). Highest: {max(drain_values):.2f}",
                )
