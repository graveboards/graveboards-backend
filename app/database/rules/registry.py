from __future__ import annotations

from typing import Any

from app.database.rules.base import RestrictionBase
from app.database.rules.validators.rate_limit import RateLimitRestriction
from app.database.rules.validators.cooldown import CooldownRestriction
from app.database.rules.validators.blacklist import BlacklistRestriction
from app.database.rules.validators.beatmap.duration import DurationRestriction
from app.database.rules.validators.beatmap.star_rating import StarRatingRestriction
from app.database.rules.validators.beatmap.ar_range import ARRangeRestriction
from app.database.rules.validators.beatmap.od_range import ODRangeRestriction
from app.database.rules.validators.beatmap.hp_range import HPRangeRestriction
from app.database.rules.validators.beatmap.cs_range import CSRangeRestriction
from app.database.rules.validators.beatmap.drain_range import DrainRangeRestriction
from app.database.rules.validators.beatmap.bpm import BPMRestriction
from app.database.rules.validators.beatmap.genre import GenreRestriction
from app.database.rules.validators.beatmap.language import LanguageRestriction
from app.database.rules.validators.beatmap.mode import ModeRestriction
from app.database.rules.validators.beatmap.difficulty_count import DifficultyCountRestriction
from app.database.rules.validators.beatmap.storyboard import StoryboardRestriction
from app.database.rules.validators.beatmap.video import VideoRestriction
from app.database.rules.validators.beatmap.tags import TagsRestriction
from app.database.rules.validators.beatmap.length import LengthRestriction
from app.database.rules.validators.beatmap.combinations import CombinationRestriction
from app.database.rules.validators.database.never_ranked import NeverRankedRestriction
from app.database.rules.validators.database.unique_artist_title import UniqueArtistTitleRestriction


TIER_1_VALIDATORS: dict[str, type[RestrictionBase]] = {
    RateLimitRestriction.type: RateLimitRestriction,
    CooldownRestriction.type: CooldownRestriction,
    BlacklistRestriction.type: BlacklistRestriction,
}


TIER_2_VALIDATORS: dict[str, type[RestrictionBase]] = {
    DurationRestriction.type: DurationRestriction,
    StarRatingRestriction.type: StarRatingRestriction,
    ARRangeRestriction.type: ARRangeRestriction,
    ODRangeRestriction.type: ODRangeRestriction,
    HPRangeRestriction.type: HPRangeRestriction,
    CSRangeRestriction.type: CSRangeRestriction,
    DrainRangeRestriction.type: DrainRangeRestriction,
    BPMRestriction.type: BPMRestriction,
    GenreRestriction.type: GenreRestriction,
    LanguageRestriction.type: LanguageRestriction,
    ModeRestriction.type: ModeRestriction,
    DifficultyCountRestriction.type: DifficultyCountRestriction,
    StoryboardRestriction.type: StoryboardRestriction,
    VideoRestriction.type: VideoRestriction,
    TagsRestriction.type: TagsRestriction,
    LengthRestriction.type: LengthRestriction,
    CombinationRestriction.type: CombinationRestriction,
}


TIER_3_VALIDATORS: dict[str, type[RestrictionBase]] = {
    NeverRankedRestriction.type: NeverRankedRestriction,
    UniqueArtistTitleRestriction.type: UniqueArtistTitleRestriction,
}


RULE_REGISTRY: dict[str, type[RestrictionBase]] = {
    **TIER_1_VALIDATORS,
    **TIER_2_VALIDATORS,
    **TIER_3_VALIDATORS,
}


RULE_TIERS: dict[str, int] = {
    "rate_limit": 1,
    "cooldown": 1,
    "blacklist": 1,
    "beatmap_duration": 2,
    "beatmap_star_rating": 2,
    "beatmap_ar_range": 2,
    "beatmap_od_range": 2,
    "beatmap_hp_range": 2,
    "beatmap_cs_range": 2,
    "beatmap_drain_range": 2,
    "beatmap_bpm": 2,
    "beatmap_genre": 2,
    "beatmap_language": 2,
    "beatmap_mode": 2,
    "beatmap_difficulty_count": 2,
    "beatmap_storyboard": 2,
    "beatmap_video": 2,
    "beatmap_tags": 2,
    "beatmap_length": 2,
    "beatmap_combination": 2,
    "never_ranked": 3,
    "unique_artist_title": 3,
}


def get_validator(type: str) -> type[RestrictionBase] | None:
    return RULE_REGISTRY.get(type)


def get_validator_tier(type: str) -> int | None:
    return RULE_TIERS.get(type)


def effective_rule_tier(rule_type: str, config: dict) -> int:
    """Return the phase/tier a rule should execute in, accounting for composites.

    A composite's execution tier is the max tier of its descendants, so a
    composite containing a Tier-3 (osu! API backed) rule runs in Phase 2 (async,
    timeout-guarded) instead of synchronously on the Phase-1 request path. Plain
    rules use their registered tier (defaulting to 2 when unknown).
    """
    if rule_type == "composite":
        children = (config or {}).get("rules", []) or []
        child_tiers = [
            effective_rule_tier(child.get("type", ""), child.get("config", {}) or {})
            for child in children
        ]
        # A composite is at least Tier 2 (it runs beatmap-style logic); bump to the
        # highest descendant tier so Tier-3 descendants push it into Phase 2.
        return max([2, *child_tiers])

    return RULE_TIERS.get(rule_type, 2)


def register_validator(
    type: str,
    validator_class: type[RestrictionBase],
    tier: int = 1,
) -> None:
    RULE_REGISTRY[type] = validator_class
    RULE_TIERS[type] = tier


def get_validators_for_tier(tier: int) -> dict[str, type[RestrictionBase]]:
    return {
        type_name: validator_cls
        for type_name, validator_cls in RULE_REGISTRY.items()
        if RULE_TIERS.get(type_name) == tier
    }


def get_supported_versions(type: str) -> set[str] | None:
    validator_cls = RULE_REGISTRY.get(type)
    if validator_cls is None:
        return None
    return validator_cls.supported_versions
