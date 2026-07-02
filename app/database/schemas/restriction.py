from datetime import datetime
from typing import Optional, Literal, Any

from pydantic import BaseModel, field_validator
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra


RestrictionType = Literal["rate_limit", "cooldown", "blacklist"]
RestrictionScope = Literal[
    "user",
    "beatmapset_type",
    "artist",
    "creator",
    "custom",
]


class RateLimitConfig(BaseModel):
    max_requests: int
    period: str
    scope: RestrictionScope = "user"
    target: Optional[list[int]] = None

    @field_validator("max_requests")
    @classmethod
    def validate_max_requests(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_requests must be at least 1")
        return v

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        valid_periods = {"day", "week", "month", "year"}
        if not v.isdigit() and v not in valid_periods:
            raise ValueError(
                f"period must be one of {sorted(valid_periods)} or a positive integer (seconds)"
            )
        return v


class CooldownConfig(BaseModel):
    cooldown_seconds: int
    scope: RestrictionScope = "user"
    target: Optional[list[int]] = None

    @field_validator("cooldown_seconds")
    @classmethod
    def validate_cooldown(cls, v: int) -> int:
        if v < 1:
            raise ValueError("cooldown_seconds must be at least 1")
        return v


class BlacklistConfig(BaseModel):
    scope: RestrictionScope = "user"
    target: list[int] = []


RestrictionConfig = RateLimitConfig | CooldownConfig | BlacklistConfig


class RestrictionSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    queue_id: int
    restriction_type: RestrictionType
    config: dict[str, Any] = {}
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime]


class RestrictionCreateSchema(BaseModel):
    restriction_type: RestrictionType
    config: dict[str, Any]

    @field_validator("config")
    @classmethod
    def validate_config_by_type(cls, v: dict[str, Any], info) -> dict[str, Any]:
        restriction_type = info.data.get("restriction_type")
        if not restriction_type:
            return v

        if restriction_type == "rate_limit":
            validated = RateLimitConfig(**v)
        elif restriction_type == "cooldown":
            validated = CooldownConfig(**v)
        elif restriction_type == "blacklist":
            validated = BlacklistConfig(**v)
        else:
            return v

        return validated.model_dump(exclude_none=True)


class RestrictionUpdateSchema(BaseModel):
    id: Optional[int] = None
    is_active: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
