from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import HPRangeConfig


class HPRangeRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_hp_range"
    config_schema = HPRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RestrictionViolationError(
                self.restriction_type,
                "No beatmaps available in beatmapset",
            )

        hp_values = [b.drain for b in beatmaps]
        min_hp = config.get("min")
        max_hp = config.get("max")

        if logic == "all":
            for beatmap, hp in zip(beatmaps, hp_values):
                if min_hp is not None and hp < min_hp:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' HP ({hp:.2f}) is below "
                        f"minimum allowed HP ({min_hp:.2f})",
                    )
                if max_hp is not None and hp > max_hp:
                    raise RestrictionViolationError(
                        self.restriction_type,
                        f"Beatmap '{beatmap.version}' HP ({hp:.2f}) exceeds "
                        f"maximum allowed HP ({max_hp:.2f})",
                    )
        else:
            if min_hp is not None and min(hp_values) < min_hp:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have HP below minimum allowed "
                    f"({min_hp:.2f}). Lowest: {min(hp_values):.2f}",
                )
            if max_hp is not None and max(hp_values) > max_hp:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Some beatmaps have HP above maximum allowed "
                    f"({max_hp:.2f}). Highest: {max(hp_values):.2f}",
                )
