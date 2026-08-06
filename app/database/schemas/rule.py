"""Pydantic schemas for queue rules."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, field_validator, model_validator
from pydantic.config import ConfigDict
from pydantic_core.core_schema import ValidationInfo

from app.osu_api.literals import (
    GenreIdLiteral,
    LanguageIdLiteral,
    RulesetLiteral,
)

from .base_model_extra import BaseModelExtra

RuleType = Literal[
    "rate_limit",
    "cooldown",
    "blacklist",
    "beatmap_duration",
    "beatmap_star_rating",
    "beatmap_ar_range",
    "beatmap_od_range",
    "beatmap_hp_range",
    "beatmap_cs_range",
    "beatmap_drain_range",
    "beatmap_bpm",
    "beatmap_genre",
    "beatmap_language",
    "beatmap_mode",
    "beatmap_difficulty_count",
    "beatmap_storyboard",
    "beatmap_video",
    "beatmap_tags",
    "beatmap_length",
    "composite",
    "never_ranked",
    "unique_artist_title",
]
RuleScope = Literal["user"]


class _StrictConfig(BaseModel):
    """Base model that rejects unknown fields for rule configs."""

    model_config = ConfigDict(extra="forbid")


def _validate_target_ids(v: list[int] | None) -> list[int] | None:
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
    """Per-period request cap applied to matching users."""

    max_requests: int
    period: str
    scope: RuleScope = "user"
    target: list[int] | None = None

    @field_validator("max_requests")
    @classmethod
    def validate_max_requests(cls, v: int) -> int:
        """Ensure the request cap is at least one."""
        if v < 1:
            raise ValueError("max_requests must be at least 1")
        return v

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        """Allow a known period name or a positive number of seconds."""
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
    """Wait period applied between matching user actions."""

    cooldown_seconds: int
    scope: RuleScope = "user"
    target: list[int] | None = None

    @field_validator("cooldown_seconds")
    @classmethod
    def validate_cooldown(cls, v: int) -> int:
        """Ensure the cooldown duration is at least one second."""
        if v < 1:
            raise ValueError("cooldown_seconds must be at least 1")
        return v

    _validate_target = field_validator("target")(_validate_target_ids)


class BlacklistConfig(_StrictConfig):
    """Set of users to exclude from a queue."""

    scope: RuleScope = "user"
    target: list[int]

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: list[int]) -> list[int] | None:
        """Ensure the blacklist is non-empty and well-formed."""
        if not v:
            raise ValueError("blacklist target must contain at least one user ID")
        return _validate_target_ids(v)


# ── Tier 2 configs ──────────────────────────────────────────────


class DurationConfig(_StrictConfig):
    """Bounds on a beatmap's duration for matching."""

    min_seconds: int | None = None
    max_seconds: int | None = None
    logic: Literal["max", "min", "all"] = "max"

    @field_validator("min_seconds", "max_seconds")
    @classmethod
    def validate_non_negative(cls, v: int | None) -> int | None:
        """Enforce non-negative duration bounds."""
        if v is not None and v < 0:
            raise ValueError("duration bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Require a bound and keep the minimum at or below the maximum."""
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
    """Bounds on a beatmap's star rating for matching."""

    min: float | None = None
    max: float | None = None
    logic: Literal["max", "min", "all", "any"] = "any"

    @field_validator("min", "max")
    @classmethod
    def validate_non_negative(cls, v: float | None) -> float | None:
        """Enforce non-negative star rating bounds."""
        if v is not None and v < 0:
            raise ValueError("star rating bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Require a bound and keep the minimum at or below the maximum."""
        if self.min is None and self.max is None:
            raise ValueError("at least one of min/max is required")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class RangeConfig(_StrictConfig):
    """Numeric bounds shared by stat range rule configs."""

    min: float | None = None
    max: float | None = None

    @field_validator("min")
    @classmethod
    def validate_min(cls, v: float | None) -> float | None:
        """Enforce a non-negative minimum."""
        if v is not None and v < 0:
            raise ValueError("min must be non-negative")
        return v

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: float | None) -> float | None:
        """Enforce a non-negative maximum."""
        if v is not None and v < 0:
            raise ValueError("max must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Require a bound and keep the minimum at or below the maximum."""
        if self.min is None and self.max is None:
            raise ValueError("at least one of min/max is required")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class ARRangeConfig(RangeConfig):
    """Approach rate range rule config."""

    logic: Literal["any", "all"] = "any"


class ODRangeConfig(RangeConfig):
    """Overall difficulty range rule config."""

    logic: Literal["any", "all"] = "any"


class HPRangeConfig(RangeConfig):
    """HP drain range rule config."""

    logic: Literal["any", "all"] = "any"


class CSRangeConfig(RangeConfig):
    """Circle size range rule config."""

    logic: Literal["any", "all"] = "any"


class DrainRangeConfig(RangeConfig):
    """Drain time range rule config."""

    logic: Literal["any", "all"] = "any"


class BPMConfig(_StrictConfig):
    """Bounds on a beatmap's BPM for matching."""

    min_bpm: float | None = None
    max_bpm: float | None = None
    logic: Literal["any", "all", "avg"] = "any"

    @field_validator("min_bpm", "max_bpm")
    @classmethod
    def validate_non_negative(cls, v: float | None) -> float | None:
        """Enforce non-negative BPM bounds."""
        if v is not None and v < 0:
            raise ValueError("BPM bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Require a bound and keep the minimum at or below the maximum."""
        if self.min_bpm is None and self.max_bpm is None:
            raise ValueError("at least one of min_bpm/max_bpm is required")
        if self.min_bpm is not None and self.max_bpm is not None and self.min_bpm > self.max_bpm:
            raise ValueError("min_bpm must be <= max_bpm")
        return self


class GenreConfig(_StrictConfig):
    """Set of genres a beating map must belong to."""

    genre_ids: list[GenreIdLiteral]

    @field_validator("genre_ids")
    @classmethod
    def validate_non_empty(cls, v: list[int]) -> list[int]:
        """Require at least one genre identifier."""
        if not v:
            raise ValueError("genre_ids must contain at least one genre")
        return v


class LanguageConfig(_StrictConfig):
    """Set of languages a beatmap must belong to."""

    language_ids: list[LanguageIdLiteral]

    @field_validator("language_ids")
    @classmethod
    def validate_non_empty(cls, v: list[int]) -> list[int]:
        """Require at least one language identifier."""
        if not v:
            raise ValueError("language_ids must contain at least one language")
        return v


class ModeConfig(_StrictConfig):
    """Set of game modes allowed by the rule."""

    allowed_modes: list[RulesetLiteral]

    @field_validator("allowed_modes")
    @classmethod
    def validate_modes(cls, v: list[str]) -> list[str]:
        """Require at least one allowed mode."""
        if not v:
            raise ValueError("allowed_modes must contain at least one mode")
        return v


class DifficultyCountConfig(_StrictConfig):
    """Bounds on the number of difficulties in a beatmapset."""

    min: int | None = None
    max: int | None = None

    @field_validator("min")
    @classmethod
    def validate_min(cls, v: int | None) -> int | None:
        """Ensure the minimum count is at least one."""
        if v is not None and v < 1:
            raise ValueError("min must be at least 1")
        return v

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: int | None) -> int | None:
        """Ensure the maximum count is at least one."""
        if v is not None and v < 1:
            raise ValueError("max must be at least 1")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Require a count bound and keep the minimum at or below the maximum."""
        if self.min is None and self.max is None:
            raise ValueError("at least one of min/max is required")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be <= max")
        return self


class StoryboardConfig(_StrictConfig):
    """Whether a beatmapset must have a storyboard."""

    allowed: bool


class VideoConfig(_StrictConfig):
    """Whether a beatmapset must have a video."""

    allowed: bool


class TagsConfig(_StrictConfig):
    """Set of tags a beatmapset must carry."""

    tag_ids: list[int]
    logic: Literal["any", "all"] = "any"

    @field_validator("tag_ids")
    @classmethod
    def validate_tag_ids(cls, v: list[int]) -> list[int]:
        """Require at least one well-formed tag identifier."""
        if not v:
            raise ValueError("tag_ids must contain at least one tag")
        for tag_id in v:
            if tag_id < 1:
                raise ValueError("tag IDs must be positive")
        return v


class LengthConfig(_StrictConfig):
    """Bounds on a beatmap's hit or total length."""

    min_hit_length: int | None = None
    max_hit_length: int | None = None
    min_total_length: int | None = None
    max_total_length: int | None = None
    logic: Literal["any", "all"] = "any"

    @field_validator("min_hit_length", "max_hit_length", "min_total_length", "max_total_length")
    @classmethod
    def validate_non_negative(cls, v: int | None) -> int | None:
        """Enforce non-negative length bounds."""
        if v is not None and v < 0:
            raise ValueError("length bounds must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Require a length bound and keep each minimum at or below its maximum."""
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


_COMPOSITE_DISALLOWED_CHILD_TYPES = frozenset({"rate_limit", "cooldown", "blacklist"})
_MAX_COMPOSITE_DEPTH = 10


class CompositeConfig(_StrictConfig):
    """Boolean combination of nested rule configs."""

    operator: Literal["and", "or", "not"]
    rules: list[dict[str, Any]]

    @model_validator(mode="after")
    def validate_composite(self) -> Self:
        """Validate the composite tree structure."""
        _validate_composite_tree(self.operator, self.rules, depth=1)
        return self


def _validate_composite_tree(operator: str, rules: list[dict[str, Any]], depth: int) -> None:
    if depth > _MAX_COMPOSITE_DEPTH:
        raise ValueError(f"composite nesting depth exceeds maximum ({_MAX_COMPOSITE_DEPTH})")
    if not rules:
        raise ValueError("composite rules must contain at least one rule")
    if operator == "not" and len(rules) != 1:
        raise ValueError("NOT operator requires exactly one child rule")

    for i, child in enumerate(rules):
        child_type: str | None = child.get("type")
        if not child_type:
            raise ValueError(f"Rule at index {i} missing 'type' field")

        if child_type in _COMPOSITE_DISALLOWED_CHILD_TYPES:
            raise ValueError(f"Rule type '{child_type}' cannot be used inside a composite")

        child_config = child.get("config", {})

        if child_type == "composite":
            child_operator = child_config.get("operator")
            if child_operator not in ("and", "or", "not"):
                raise ValueError(f"Unknown composite operator: {child_operator}")
            _validate_composite_tree(child_operator, child_config.get("rules", []), depth + 1)
            continue

        if child_type not in RULE_CONFIG_SCHEMA_MAP:
            raise ValueError(f"Unknown rule type in composite: '{child_type}'")

        # Validate the child config against its own type schema.
        validate_rule_config(child_type, child_config)


class NeverRankedConfig(_StrictConfig):
    """Require that a beatmapset has never been ranked."""

    ruleset: Literal["osu", "taiko", "fruits", "mania"] = "osu"
    normalize_versions: bool = True


class UniqueArtistTitleConfig(_StrictConfig):
    """Require a unique artist/title combination."""

    normalize_versions: bool = True


# ── Union types ─────────────────────────────────────────────────


Tier1Config = RateLimitConfig | CooldownConfig | BlacklistConfig
Tier2Config = (
    DurationConfig
    | StarRatingConfig
    | ARRangeConfig
    | ODRangeConfig
    | HPRangeConfig
    | CSRangeConfig
    | DrainRangeConfig
    | BPMConfig
    | GenreConfig
    | LanguageConfig
    | ModeConfig
    | DifficultyCountConfig
    | StoryboardConfig
    | VideoConfig
    | TagsConfig
    | LengthConfig
    | CompositeConfig
)
Tier3Config = NeverRankedConfig | UniqueArtistTitleConfig

RuleConfig = Tier1Config | Tier2Config | Tier3Config


# ── ORM / API schemas ───────────────────────────────────────────


class RuleSchema(BaseModel, BaseModelExtra):
    """Rule record stored against a queue."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    queue_id: int
    type: RuleType
    config: dict[str, Any] = {}
    is_active: bool | None = None
    is_public: bool | None = None
    version: str = "1.0"
    created_at: datetime | None = None
    updated_at: datetime | None


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
    ------
        pydantic.ValidationError:
            If the config does not satisfy the type's schema.
    """
    schema_cls = RULE_CONFIG_SCHEMA_MAP.get(rule_type)
    if schema_cls:
        return schema_cls(**config).model_dump(exclude_none=True)
    return config


class RuleCreateSchema(BaseModel):
    """Fields required to create a rule."""

    type: RuleType
    config: dict[str, Any]
    is_public: bool = True
    version: str = "1.0"

    @field_validator("config")
    @classmethod
    def validate_config_by_type(cls, v: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        """Validate config against the schema for its declared type."""
        type_: str | None = info.data.get("type")
        if not type_:
            return v

        return validate_rule_config(type_, v)


class RuleReplaceSchema(RuleCreateSchema):
    """Fields for replacing a rule."""

    is_active: bool = True


class RuleUpdateSchema(BaseModel):
    """Updatable fields for an existing rule."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool | None = None
    is_public: bool | None = None
    config: dict[str, Any] | None = None
    version: str | None = None
