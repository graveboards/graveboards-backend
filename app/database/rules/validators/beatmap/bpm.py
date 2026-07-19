from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import BPMConfig


class BPMRestriction(BeatmapRestrictionBase):
    type = "beatmap_bpm"
    config_schema = BPMConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []
        beatmapset = context.beatmapset

        if not beatmaps:
            raise RuleViolationError(
                self.type,
                "No beatmaps available in beatmapset",
            )

        min_bpm = config.get("min_bpm")
        max_bpm = config.get("max_bpm")

        if logic == "avg":
            avg_bpm = sum(b.bpm for b in beatmaps) / len(beatmaps) if beatmaps else beatmapset.bpm if beatmapset else 0.0
            if min_bpm is not None and avg_bpm < min_bpm:
                raise RuleViolationError(
                    self.type,
                    f"Average BPM ({avg_bpm:.2f}) is below minimum allowed "
                    f"({min_bpm:.2f})",
                )
            if max_bpm is not None and avg_bpm > max_bpm:
                raise RuleViolationError(
                    self.type,
                    f"Average BPM ({avg_bpm:.2f}) exceeds maximum allowed "
                    f"({max_bpm:.2f})",
                )

        elif logic == "all":
            for beatmap in beatmaps:
                if min_bpm is not None and beatmap.bpm < min_bpm:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' BPM ({beatmap.bpm:.2f}) "
                        f"is below minimum allowed ({min_bpm:.2f})",
                    )
                if max_bpm is not None and beatmap.bpm > max_bpm:
                    raise RuleViolationError(
                        self.type,
                        f"Beatmap '{beatmap.version}' BPM ({beatmap.bpm:.2f}) "
                        f"exceeds maximum allowed ({max_bpm:.2f})",
                    )

        else:
            # logic == "any": at least one beatmap must fall within the range.
            beatmap_bmps = [b.bpm for b in beatmaps]
            matched = any(
                (min_bpm is None or bpm >= min_bpm) and (max_bpm is None or bpm <= max_bpm)
                for bpm in beatmap_bmps
            )
            if not matched:
                raise RuleViolationError(
                    self.type,
                    f"No beatmap has BPM within the allowed range "
                    f"(min={min_bpm}, max={max_bpm}). "
                    f"Values: {[round(v, 2) for v in beatmap_bmps]}",
                )
