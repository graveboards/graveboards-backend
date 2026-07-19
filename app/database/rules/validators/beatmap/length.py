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
            # logic == "any": at least one beatmap must satisfy every configured bound.
            def within_bounds(beatmap) -> bool:
                if min_hit_length is not None and beatmap.hit_length < min_hit_length:
                    return False
                if max_hit_length is not None and beatmap.hit_length > max_hit_length:
                    return False
                if min_total_length is not None and beatmap.total_length < min_total_length:
                    return False
                if max_total_length is not None and beatmap.total_length > max_total_length:
                    return False
                return True

            if not any(within_bounds(b) for b in beatmaps):
                raise RuleViolationError(
                    self.type,
                    "No beatmap satisfies the configured length range "
                    f"(hit_length {min_hit_length}-{max_hit_length}s, "
                    f"total_length {min_total_length}-{max_total_length}s)",
                )
