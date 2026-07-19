from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import ARRangeConfig


class ARRangeRestriction(BeatmapRestrictionBase):
    type = "beatmap_ar_range"
    config_schema = ARRangeConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        ar_values = [b.ar for b in beatmaps]
        min_ar = config.get("min")
        max_ar = config.get("max")

        if logic == "all":
            for beatmap, ar in zip(beatmaps, ar_values):
                if min_ar is not None and ar < min_ar:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' AR ({ar:.2f}) is below "
                        f"minimum allowed AR ({min_ar:.2f})",
                    )
                if max_ar is not None and ar > max_ar:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' AR ({ar:.2f}) exceeds "
                        f"maximum allowed AR ({max_ar:.2f})",
                    )
        else:
            # logic == "any": at least one beatmap must fall within the range.
            matched = any(
                (min_ar is None or ar >= min_ar) and (max_ar is None or ar <= max_ar)
                for ar in ar_values
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has AR within the allowed range "
                    f"(min={min_ar}, max={max_ar}). "
                    f"Values: {[round(v, 2) for v in ar_values]}",
                )
