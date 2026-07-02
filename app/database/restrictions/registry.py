from app.database.restrictions.validators.rate_limit import RateLimitRestriction
from app.database.restrictions.validators.cooldown import CooldownRestriction
from app.database.restrictions.validators.blacklist import BlacklistRestriction


RESTRICTION_REGISTRY: dict[str, type] = {
    RateLimitRestriction.restriction_type: RateLimitRestriction,
    CooldownRestriction.restriction_type: CooldownRestriction,
    BlacklistRestriction.restriction_type: BlacklistRestriction,
}


def get_validator(restriction_type: str) -> type | None:
    return RESTRICTION_REGISTRY.get(restriction_type)


def register_validator(restriction_type: str, validator_class: type) -> None:
    RESTRICTION_REGISTRY[restriction_type] = validator_class
