from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import HPRangeConfig


class HPRangeRestriction(BeatmapRestrictionBase):
    type = "beatmap_hp_range"
    config_schema = HPRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        hp_values = [b.drain for b in beatmaps]
        min_hp = config.get("min")
        max_hp = config.get("max")

        if logic == "all":
            for beatmap, hp in zip(beatmaps, hp_values):
                if min_hp is not None and hp < min_hp:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' HP ({hp:.2f}) is below "
                        f"minimum allowed HP ({min_hp:.2f})",
                    )
                if max_hp is not None and hp > max_hp:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' HP ({hp:.2f}) exceeds "
                        f"maximum allowed HP ({max_hp:.2f})",
                    )
        else:
            # logic == "any": at least one beatmap must fall within the range.
            matched = any(
                (min_hp is None or hp >= min_hp) and (max_hp is None or hp <= max_hp)
                for hp in hp_values
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has HP within the allowed range "
                    f"(min={min_hp}, max={max_hp}). "
                    f"Values: {[round(v, 2) for v in hp_values]}",
                )
