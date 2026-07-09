from __future__ import annotations

from typing import Any

from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.validators.metadata.song_identity import MetadataProvider


class BeatmapStatsProvider(MetadataProvider):
    @property
    def name(self) -> str:
        return "beatmap_stats"

    async def resolve(self, context: ExecutionContext) -> dict[str, Any]:
        beatmaps = context.beatmaps or []

        if not beatmaps:
            return {
                "min_sr": 0.0,
                "max_sr": 0.0,
                "avg_sr": 0.0,
                "min_ar": 0.0,
                "max_ar": 0.0,
                "avg_ar": 0.0,
                "min_od": 0.0,
                "max_od": 0.0,
                "avg_od": 0.0,
                "min_hp": 0.0,
                "max_hp": 0.0,
                "avg_hp": 0.0,
                "min_drain": 0.0,
                "max_drain": 0.0,
                "avg_drain": 0.0,
                "min_bpm": 0.0,
                "max_bpm": 0.0,
                "avg_bpm": 0.0,
                "difficulty_count": 0,
                "modes": [],
            }

        srs = [b.difficulty_rating for b in beatmaps]
        ars = [b.ar for b in beatmaps]
        ods = [b.accuracy for b in beatmaps]
        hps = [b.drain for b in beatmaps]
        drains = [b.drain for b in beatmaps]
        bmps = [b.bpm for b in beatmaps]
        modes = list({b.mode for b in beatmaps})

        n = len(beatmaps)

        return {
            "min_sr": min(srs),
            "max_sr": max(srs),
            "avg_sr": sum(srs) / n,
            "min_ar": min(ars),
            "max_ar": max(ars),
            "avg_ar": sum(ars) / n,
            "min_od": min(ods),
            "max_od": max(ods),
            "avg_od": sum(ods) / n,
            "min_hp": min(hps),
            "max_hp": max(hps),
            "avg_hp": sum(hps) / n,
            "min_drain": min(drains),
            "max_drain": max(drains),
            "avg_drain": sum(drains) / n,
            "min_bpm": min(bmps),
            "max_bpm": max(bmps),
            "avg_bpm": sum(bmps) / n,
            "difficulty_count": n,
            "modes": modes,
        }
