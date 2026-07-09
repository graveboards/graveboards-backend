from __future__ import annotations

from typing import Any

from app.database.restrictions.base import RestrictionBase
from app.database.restrictions.validators.rate_limit import RateLimitRestriction
from app.database.restrictions.validators.cooldown import CooldownRestriction
from app.database.restrictions.validators.blacklist import BlacklistRestriction
from app.database.restrictions.validators.beatmap.duration import DurationRestriction
from app.database.restrictions.validators.beatmap.star_rating import StarRatingRestriction
from app.database.restrictions.validators.beatmap.ar_range import ARRangeRestriction
from app.database.restrictions.validators.beatmap.od_range import ODRangeRestriction
from app.database.restrictions.validators.beatmap.hp_range import HPRangeRestriction
from app.database.restrictions.validators.beatmap.cs_range import CSRangeRestriction
from app.database.restrictions.validators.beatmap.drain_range import DrainRangeRestriction
from app.database.restrictions.validators.beatmap.bpm import BPMRestriction
from app.database.restrictions.validators.beatmap.genre import GenreRestriction
from app.database.restrictions.validators.beatmap.language import LanguageRestriction
from app.database.restrictions.validators.beatmap.mode import ModeRestriction
from app.database.restrictions.validators.beatmap.difficulty_count import DifficultyCountRestriction
from app.database.restrictions.validators.beatmap.storyboard import StoryboardRestriction
from app.database.restrictions.validators.beatmap.video import VideoRestriction
from app.database.restrictions.validators.beatmap.tags import TagsRestriction
from app.database.restrictions.validators.beatmap.length import LengthRestriction
from app.database.restrictions.validators.beatmap.combinations import CombinationRestriction


TIER_1_VALIDATORS: dict[str, type[RestrictionBase]] = {
    RateLimitRestriction.restriction_type: RateLimitRestriction,
    CooldownRestriction.restriction_type: CooldownRestriction,
    BlacklistRestriction.restriction_type: BlacklistRestriction,
}


TIER_2_VALIDATORS: dict[str, type[RestrictionBase]] = {
    DurationRestriction.restriction_type: DurationRestriction,
    StarRatingRestriction.restriction_type: StarRatingRestriction,
    ARRangeRestriction.restriction_type: ARRangeRestriction,
    ODRangeRestriction.restriction_type: ODRangeRestriction,
    HPRangeRestriction.restriction_type: HPRangeRestriction,
    CSRangeRestriction.restriction_type: CSRangeRestriction,
    DrainRangeRestriction.restriction_type: DrainRangeRestriction,
    BPMRestriction.restriction_type: BPMRestriction,
    GenreRestriction.restriction_type: GenreRestriction,
    LanguageRestriction.restriction_type: LanguageRestriction,
    ModeRestriction.restriction_type: ModeRestriction,
    DifficultyCountRestriction.restriction_type: DifficultyCountRestriction,
    StoryboardRestriction.restriction_type: StoryboardRestriction,
    VideoRestriction.restriction_type: VideoRestriction,
    TagsRestriction.restriction_type: TagsRestriction,
    LengthRestriction.restriction_type: LengthRestriction,
    CombinationRestriction.restriction_type: CombinationRestriction,
}


RESTRICTION_REGISTRY: dict[str, type[RestrictionBase]] = {
    **TIER_1_VALIDATORS,
    **TIER_2_VALIDATORS,
}


RESTRICTION_TIERS: dict[str, int] = {
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
}


def get_validator(restriction_type: str) -> type[RestrictionBase] | None:
    return RESTRICTION_REGISTRY.get(restriction_type)


def get_validator_tier(restriction_type: str) -> int | None:
    return RESTRICTION_TIERS.get(restriction_type)


def register_validator(
    restriction_type: str,
    validator_class: type[RestrictionBase],
    tier: int = 1,
) -> None:
    RESTRICTION_REGISTRY[restriction_type] = validator_class
    RESTRICTION_TIERS[restriction_type] = tier


def get_validators_for_tier(tier: int) -> dict[str, type[RestrictionBase]]:
    return {
        type_name: validator_cls
        for type_name, validator_cls in RESTRICTION_REGISTRY.items()
        if RESTRICTION_TIERS.get(type_name) == tier
    }


def get_supported_versions(restriction_type: str) -> set[str] | None:
    validator_cls = RESTRICTION_REGISTRY.get(restriction_type)
    if validator_cls is None:
        return None
    return validator_cls.supported_versions
