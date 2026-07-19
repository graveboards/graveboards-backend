from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import StarRatingConfig


class StarRatingRestriction(BeatmapRestrictionBase):
    type = "beatmap_star_rating"
    config_schema = StarRatingConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        star_ratings = [b.difficulty_rating for b in beatmaps]
        min_sr = config.get("min")
        max_sr = config.get("max")

        if logic == "max":
            highest = max(star_ratings)
            if max_sr is not None and highest > max_sr:
                raise RuleViolationError(
                    self.type,
                    f"Highest star rating ({highest:.2f}) exceeds maximum "
                    f"allowed star rating ({max_sr:.2f})",
                )

        elif logic == "min":
            lowest = min(star_ratings)
            if min_sr is not None and lowest < min_sr:
                raise RuleViolationError(
                    self.type,
                    f"Lowest star rating ({lowest:.2f}) is below minimum "
                    f"allowed star rating ({min_sr:.2f})",
                )

        elif logic == "all":
            for beatmap, sr in zip(beatmaps, star_ratings):
                if min_sr is not None and sr < min_sr:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' star rating "
                        f"({sr:.2f}) is below minimum "
                        f"allowed star rating ({min_sr:.2f})",
                    )
                if max_sr is not None and sr > max_sr:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' star rating "
                        f"({sr:.2f}) exceeds maximum "
                        f"allowed star rating ({max_sr:.2f})",
                    )

        elif logic == "any":
            # At least one beatmap must fall within the range.
            matched = any(
                (min_sr is None or sr >= min_sr) and (max_sr is None or sr <= max_sr)
                for sr in star_ratings
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has a star rating within the allowed range "
                    f"(min={min_sr}, max={max_sr}). "
                    f"Values: {[round(v, 2) for v in star_ratings]}",
                )
