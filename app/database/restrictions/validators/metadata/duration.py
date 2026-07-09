from __future__ import annotations

from typing import Any

from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.validators.metadata.song_identity import MetadataProvider


_VERSION_MARKERS = [
    "TV Size",
    "Extended ver.",
    "Remix",
    "Cut version",
    "Nightcore ver.",
    "Radio Edit",
    "Album Edit",
    "Full ver.",
    "Instrumental",
    "Single Version",
    "Radio Version",
    "Club Mix",
    "Dub Mix",
    "Acoustic Version",
    "Live Version",
]


class DurationProvider(MetadataProvider):
    @property
    def name(self) -> str:
        return "duration"

    async def resolve(self, context: ExecutionContext) -> dict[str, Any]:
        beatmapset = context.beatmapset
        beatmaps = context.beatmaps or []

        original_duration = beatmapset.bpm if beatmapset else 0

        has_version_marker = False
        if beatmapset:
            title = beatmapset.title or ""
            title_unicode = beatmapset.title_unicode or ""
            for marker in _VERSION_MARKERS:
                if marker.lower() in title.lower() or marker.lower() in title_unicode.lower():
                    has_version_marker = True
                    break

        if beatmaps:
            total_lengths = [b.total_length for b in beatmaps]
            normalized_duration = max(total_lengths)
        else:
            normalized_duration = original_duration

        return {
            "original_duration": original_duration,
            "normalized_duration": normalized_duration,
            "has_version_marker": has_version_marker,
        }
