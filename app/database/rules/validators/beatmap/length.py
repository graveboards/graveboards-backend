from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import LengthConfig


class LengthRestriction(BeatmapRestrictionBase):
    type = "beatmap_length"
    config_schema = LengthConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        min_hit_length = config.get("min_hit_length")
        max_hit_length = config.get("max_hit_length")
        min_total_length = config.get("min_total_length")
        max_total_length = config.get("max_total_length")

        if logic == "all":
            for beatmap in beatmaps:
                if min_hit_length is not None and beatmap.hit_length < min_hit_length:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' hit length "
                        f"({beatmap.hit_length}s) is below minimum "
                        f"({min_hit_length}s)",
                    )
                if max_hit_length is not None and beatmap.hit_length > max_hit_length:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' hit length "
                        f"({beatmap.hit_length}s) exceeds maximum "
                        f"({max_hit_length}s)",
                    )
                if min_total_length is not None and beatmap.total_length < min_total_length:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' total length "
                        f"({beatmap.total_length}s) is below minimum "
                        f"({min_total_length}s)",
                    )
                if max_total_length is not None and beatmap.total_length > max_total_length:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' total length "
                        f"({beatmap.total_length}s) exceeds maximum "
                        f"({max_total_length}s)",
                    )
        else:
            hit_lengths = [b.hit_length for b in beatmaps]
            total_lengths = [b.total_length for b in beatmaps]

            if min_hit_length is not None and min(hit_lengths) < min_hit_length:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have hit length below minimum "
                    f"({min_hit_length}s). Lowest: {min(hit_lengths)}s",
                )
            if max_hit_length is not None and max(hit_lengths) > max_hit_length:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have hit length above maximum "
                    f"({max_hit_length}s). Highest: {max(hit_lengths)}s",
                )
            if min_total_length is not None and min(total_lengths) < min_total_length:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have total length below minimum "
                    f"({min_total_length}s). Lowest: {min(total_lengths)}s",
                )
            if max_total_length is not None and max(total_lengths) > max_total_length:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have total length above maximum "
                    f"({max_total_length}s). Highest: {max(total_lengths)}s",
                )
