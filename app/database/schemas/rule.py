from datetime import datetime
from typing import Optional, Literal, Any

from pydantic import BaseModel, field_validator, model_validator
from pydantic.config import ConfigDict

from app.osu_api.literals import GenreIdLiteral, LanguageIdLiteral, RulesetLiteral
from .base_model_extra import BaseModelExtra


RuleType = Literal[
    "rate_limit", "cooldown", "blacklist",
    "beatmap_duration", "beatmap_star_rating", "beatmap_ar_range",
    "beatmap_od_range", "beatmap_hp_range", "beatmap_cs_range",
    "beatmap_drain_range", "beatmap_bpm", "beatmap_genre",
    "beatmap_language", "beatmap_mode", "beatmap_difficulty_count",
    "beatmap_storyboard", "beatmap_video", "beatmap_tags",
    "beatmap_length", "composite",
    "never_ranked", "unique_artist_title",
]
RuleScope = Literal["user"]


class _StrictConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _validate_target_ids(v: Optional[list[int]]) -> Optional[list[int]]:
    if v is None:
        return v
    for target_id in v:
        if target_id < 1:
            raise ValueError("target IDs must be positive")
    if len(set(v)) != len(v):
        raise ValueError("target IDs must be unique")
    return v


# ── Tier 1 configs ──────────────────────────────────────────────


class RateLimitConfig(_StrictConfig):
    max_requests: int
    period: str
    scope: RuleScope = "user"
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
        if v.isdigit():
            if int(v) < 1:
                raise ValueError("numeric period (seconds) must be at least 1")
            return v
        if v not in valid_periods:
            raise ValueError(
                f"period must be one of {sorted(valid_periods)} or a positive integer (seconds)"
            )
        return v

    _validate_target = field_validator("target")(_validate_target_ids)


class CooldownConfig(_StrictConfig):
    cooldown_seconds: int
    scope: RuleScope = "user"
    target: Optional[list[int]] = None

    @field_validator("cooldown_seconds")
    @classmethod
    def validate_cooldown(cls, v: int) -> int:
        if v < 1:
            raise ValueError("cooldown_seconds must be at least 1")
        return v

    _validate_target = field_validator("target")(_validate_target_ids)


class BlacklistConfig(_StrictConfig):
    scope: RuleScope = "user"
    target: list[int]

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("blacklist target must contain at least one user ID")
        return _validate_target_ids(v)


# ── Tier 2 configs ──────────────────────────────────────────────


class DurationConfig(_StrictConfig):
    min_seconds: Optional[int] = None
    max_seconds: Optional[int] = None
    logic: Literal["max", "min", "all"] = "max"

    @field_validator("min_seconds", "max_seconds")
    @classmethod
    def validate_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("duration bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> "DurationConfig":
        if self.min_seconds is None and self.max_seconds is None:
            raise ValueError("at least one of min_seconds/max_seconds is required")
        if (
            self.min_seconds is not None
            and self.max_seconds is not None
            and self.min_seconds > self.max_seconds
        ):
            raise ValueError("min_seconds must be <= max_seconds")
        return self


class StarRatingConfig(_StrictConfig):
    min: Optional[float] = None
    max: Optional[float] = None
    logic: Literal["max", "min", "all", "any"] = "any"

    @field_validator("min", "max")
    @classmethod
    def validate_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("star rating bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> "StarRatingConfig":
        if self.min is None and self.max is None:
            raise ValueError("at least one of min/max is required")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class RangeConfig(_StrictConfig):
    min: Optional[float] = None
    max: Optional[float] = None

    @field_validator("min")
    @classmethod
    def validate_min(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("min must be non-negative")
        return v

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("max must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> "RangeConfig":
        if self.min is None and self.max is None:
            raise ValueError("at least one of min/max is required")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class ARRangeConfig(RangeConfig):
    logic: Literal["any", "all"] = "any"


class ODRangeConfig(RangeConfig):
    logic: Literal["any", "all"] = "any"


class HPRangeConfig(RangeConfig):
    logic: Literal["any", "all"] = "any"


class CSRangeConfig(RangeConfig):
    logic: Literal["any", "all"] = "any"


class DrainRangeConfig(RangeConfig):
    logic: Literal["any", "all"] = "any"


class BPMConfig(_StrictConfig):
    min_bpm: Optional[float] = None
    max_bpm: Optional[float] = None
    logic: Literal["any", "all", "avg"] = "any"

    @field_validator("min_bpm", "max_bpm")
    @classmethod
    def validate_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("BPM bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> "BPMConfig":
        if self.min_bpm is None and self.max_bpm is None:
            raise ValueError("at least one of min_bpm/max_bpm is required")
        if (
            self.min_bpm is not None
            and self.max_bpm is not None
            and self.min_bpm > self.max_bpm
        ):
            raise ValueError("min_bpm must be <= max_bpm")
        return self


class GenreConfig(_StrictConfig):
    genre_ids: list[GenreIdLiteral]

    @field_validator("genre_ids")
    @classmethod
    def validate_non_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("genre_ids must contain at least one genre")
        return v


class LanguageConfig(_StrictConfig):
    language_ids: list[LanguageIdLiteral]

    @field_validator("language_ids")
    @classmethod
    def validate_non_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("language_ids must contain at least one language")
        return v


class ModeConfig(_StrictConfig):
    allowed_modes: list[RulesetLiteral]

    @field_validator("allowed_modes")
    @classmethod
    def validate_modes(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("allowed_modes must contain at least one mode")
        return v


class DifficultyCountConfig(_StrictConfig):
    min: Optional[int] = None
    max: Optional[int] = None

    @field_validator("min")
    @classmethod
    def validate_min(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("min must be at least 1")
        return v

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("max must be at least 1")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> "DifficultyCountConfig":
        if self.min is None and self.max is None:
            raise ValueError("at least one of min/max is required")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class StoryboardConfig(_StrictConfig):
    allowed: bool


class VideoConfig(_StrictConfig):
    allowed: bool


class TagsConfig(_StrictConfig):
    tag_ids: list[int]
    logic: Literal["any", "all"] = "any"

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("tag_ids must contain at least one tag")
        for tag_id in v:
            if tag_id < 1:
                raise ValueError("tag IDs must be positive")
        return v


class LengthConfig(_StrictConfig):
    min_hit_length: Optional[int] = None
    max_hit_length: Optional[int] = None
    min_total_length: Optional[int] = None
    max_total_length: Optional[int] = None
    logic: Literal["any", "all"] = "any"

    @field_validator(
        "min_hit_length", "max_hit_length", "min_total_length", "max_total_length"
    )
    @classmethod
    def validate_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("length bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> "LengthConfig":
        if all(
            bound is None
            for bound in (
                self.min_hit_length,
                self.max_hit_length,
                self.min_total_length,
                self.max_total_length,
            )
        ):
            raise ValueError("at least one length bound is required")
        if (
            self.min_hit_length is not None
            and self.max_hit_length is not None
            and self.min_hit_length > self.max_hit_length
        ):
            raise ValueError("min_hit_length must be <= max_hit_length")
        if (
            self.min_total_length is not None
            and self.max_total_length is not None
            and self.min_total_length > self.max_total_length
        ):
            raise ValueError("min_total_length must be <= max_total_length")
        return self


class CompositeConfig(_StrictConfig):
    operator: Literal["and", "or", "not"]
    rules: list[dict[str, Any]]

    @field_validator("rules")
    @classmethod
    def validate_rules(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not v:
            raise ValueError("composite rules must contain at least one rule")
        for i, rule in enumerate(v):
            if "type" not in rule:
                raise ValueError(f"Rule at index {i} missing 'type' field")
        return v


class NeverRankedConfig(_StrictConfig):
    ruleset: Literal["osu", "taiko", "fruits", "mania"] = "osu"
    normalize_versions: bool = True


class UniqueArtistTitleConfig(_StrictConfig):
    normalize_versions: bool = True


# ── Union types ─────────────────────────────────────────────────


Tier1Config = RateLimitConfig | CooldownConfig | BlacklistConfig
Tier2Config = (
    DurationConfig | StarRatingConfig | ARRangeConfig | ODRangeConfig
    | HPRangeConfig | CSRangeConfig | DrainRangeConfig | BPMConfig
    | GenreConfig | LanguageConfig | ModeConfig | DifficultyCountConfig
    | StoryboardConfig | VideoConfig | TagsConfig | LengthConfig
    | CompositeConfig
)
Tier3Config = NeverRankedConfig | UniqueArtistTitleConfig

RuleConfig = Tier1Config | Tier2Config | Tier3Config


# ── ORM / API schemas ───────────────────────────────────────────


class RuleSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    queue_id: int
    type: RuleType
    config: dict[str, Any] = {}
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    version: str = "1.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime]


RULE_CONFIG_SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "rate_limit": RateLimitConfig,
    "cooldown": CooldownConfig,
    "blacklist": BlacklistConfig,
    "beatmap_duration": DurationConfig,
    "beatmap_star_rating": StarRatingConfig,
    "beatmap_ar_range": ARRangeConfig,
    "beatmap_od_range": ODRangeConfig,
    "beatmap_hp_range": HPRangeConfig,
    "beatmap_cs_range": CSRangeConfig,
    "beatmap_drain_range": DrainRangeConfig,
    "beatmap_bpm": BPMConfig,
    "beatmap_genre": GenreConfig,
    "beatmap_language": LanguageConfig,
    "beatmap_mode": ModeConfig,
    "beatmap_difficulty_count": DifficultyCountConfig,
    "beatmap_storyboard": StoryboardConfig,
    "beatmap_video": VideoConfig,
    "beatmap_tags": TagsConfig,
    "beatmap_length": LengthConfig,
    "composite": CompositeConfig,
    "never_ranked": NeverRankedConfig,
    "unique_artist_title": UniqueArtistTitleConfig,
}


def validate_rule_config(rule_type: str, config: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a rule config against its type-specific schema.

    Shared by create and update paths so a config is validated against the same
    schema regardless of how it enters the system. Rule types without a dedicated
    config schema pass through unchanged.

    Raises:
        pydantic.ValidationError:
            If the config does not satisfy the type's schema.
    """
    schema_cls = RULE_CONFIG_SCHEMA_MAP.get(rule_type)
    if schema_cls:
        return schema_cls(**config).model_dump(exclude_none=True)
    return config


class RuleCreateSchema(BaseModel):
    type: RuleType
    config: dict[str, Any]
    is_public: bool = True
    version: str = "1.0"

    @field_validator("config")
    @classmethod
    def validate_config_by_type(
        cls, v: dict[str, Any], info
    ) -> dict[str, Any]:
        type = info.data.get("type")
        if not type:
            return v

        return validate_rule_config(type, v)


class RuleUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    version: Optional[str] = None
