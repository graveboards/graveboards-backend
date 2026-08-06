"""Metadata providers used by Tier-3 restrictions."""

from __future__ import annotations

from app.database.rules.validators.metadata.beatmap_stats import BeatmapStatsProvider
from app.database.rules.validators.metadata.creator_identity import CreatorIdentityProvider
from app.database.rules.validators.metadata.duration import DurationProvider
from app.database.rules.validators.metadata.song_identity import SongIdentityProvider

__all__ = [
    "BeatmapStatsProvider",
    "CreatorIdentityProvider",
    "DurationProvider",
    "SongIdentityProvider",
]
