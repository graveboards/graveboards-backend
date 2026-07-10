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
            beatmap_bmps = [b.bpm for b in beatmaps]
            if min_bpm is not None and min(beatmap_bmps) < min_bpm:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have BPM below minimum allowed "
                    f"({min_bpm:.2f}). Lowest: {min(beatmap_bmps):.2f}",
                )
            if max_bpm is not None and max(beatmap_bmps) > max_bpm:
                raise RuleViolationError(
                    self.type,
                    f"Some beatmaps have BPM above maximum allowed "
                    f"({max_bpm:.2f}). Highest: {max(beatmap_bmps):.2f}",
                )
