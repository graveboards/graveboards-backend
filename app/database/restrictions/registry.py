from __future__ import annotations

from typing import Any

from app.database.restrictions.base import RestrictionBase
from app.database.restrictions.validators.rate_limit import RateLimitRestriction
from app.database.restrictions.validators.cooldown import CooldownRestriction
from app.database.restrictions.validators.blacklist import BlacklistRestriction


TIER_1_VALIDATORS: dict[str, type[RestrictionBase]] = {
    RateLimitRestriction.restriction_type: RateLimitRestriction,
    CooldownRestriction.restriction_type: CooldownRestriction,
    BlacklistRestriction.restriction_type: BlacklistRestriction,
}


RESTRICTION_REGISTRY: dict[str, type[RestrictionBase]] = {
    **TIER_1_VALIDATORS,
}


RESTRICTION_TIERS: dict[str, int] = {
    "rate_limit": 1,
    "cooldown": 1,
    "blacklist": 1,
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
