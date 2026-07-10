from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from app.database.rules.context import ExecutionContext


_VERSION_MARKER_PATTERN = re.compile(
    r"\(?(?:"
    r"TV Size"
    r"|Extended ver\.?"
    r"|Remix"
    r"|Cut version"
    r"|Nightcore ver\.?"
    r"|Radio Edit"
    r"|Album Edit"
    r"|Full ver\.?"
    r"|Instrumental"
    r"|Single Version"
    r"|Radio Version"
    r"|7\"? Version"
    r"|12\"? Version"
    r"|Club Mix"
    r"|Dub Mix"
    r"|Acoustic Version"
    r"|Live Version"
    r")\)?\.?\s*$",
    re.IGNORECASE,
)

_PUNCTUATION_PATTERN = re.compile(r"[^\w\s-]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    text = _VERSION_MARKER_PATTERN.sub("", text)
    text = _PUNCTUATION_PATTERN.sub("", text)
    text = _WHITESPACE_PATTERN.sub(" ", text).strip()
    return text


class MetadataProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def resolve(self, context: ExecutionContext) -> dict[str, Any]:
        ...


class SongIdentityProvider(MetadataProvider):
    @property
    def name(self) -> str:
        return "song_identity"

    async def resolve(self, context: ExecutionContext) -> dict[str, Any]:
        beatmapset = context.beatmapset
        if beatmapset is None:
            return {
                "artist": "",
                "artist_unicode": "",
                "title": "",
                "title_unicode": "",
                "normalized_artist": "",
                "normalized_title": "",
                "duration": 0,
            }

        artist = beatmapset.artist or ""
        artist_unicode = beatmapset.artist_unicode or ""
        title = beatmapset.title or ""
        title_unicode = beatmapset.title_unicode or ""

        normalized_artist = _normalize_text(artist)
        normalized_title = _normalize_text(title)

        if artist_unicode and artist_unicode != artist:
            normalized_artist_unicode = _normalize_text(artist_unicode)
            normalized_title_unicode = _normalize_text(title_unicode)
        else:
            normalized_artist_unicode = normalized_artist
            normalized_title_unicode = normalized_title

        duration = beatmapset.bpm if hasattr(beatmapset, "bpm") else 0

        return {
            "artist": artist,
            "artist_unicode": artist_unicode,
            "title": title,
            "title_unicode": title_unicode,
            "normalized_artist": normalized_artist,
            "normalized_title": normalized_title,
            "normalized_artist_unicode": normalized_artist_unicode,
            "normalized_title_unicode": normalized_title_unicode,
            "duration": duration,
        }
