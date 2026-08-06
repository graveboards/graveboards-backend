"""Concrete rule restrictions (Tier-1/2 entry points)."""

from __future__ import annotations

from app.database.rules.validators.beatmap import (
    ARRangeRestriction,
    BPMRestriction,
    CombinationRestriction,
    CSRangeRestriction,
    DifficultyCountRestriction,
    DrainRangeRestriction,
    DurationRestriction,
    GenreRestriction,
    HPRangeRestriction,
    LanguageRestriction,
    LengthRestriction,
    ModeRestriction,
    ODRangeRestriction,
    StarRatingRestriction,
    StoryboardRestriction,
    TagsRestriction,
    VideoRestriction,
)
from app.database.rules.validators.blacklist import BlacklistRestriction
from app.database.rules.validators.cooldown import CooldownRestriction
from app.database.rules.validators.rate_limit import RateLimitRestriction

__all__ = [
    "ARRangeRestriction",
    "BPMRestriction",
    "BlacklistRestriction",
    "CSRangeRestriction",
    "CombinationRestriction",
    "CooldownRestriction",
    "DifficultyCountRestriction",
    "DrainRangeRestriction",
    "DurationRestriction",
    "GenreRestriction",
    "HPRangeRestriction",
    "LanguageRestriction",
    "LengthRestriction",
    "ModeRestriction",
    "ODRangeRestriction",
    "RateLimitRestriction",
    "StarRatingRestriction",
    "StoryboardRestriction",
    "TagsRestriction",
    "VideoRestriction",
]
