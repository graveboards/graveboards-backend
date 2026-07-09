from datetime import datetime
from typing import Optional, Literal, Any

from pydantic import BaseModel, field_validator
from pydantic.config import ConfigDict

from app.osu_api.literals import GenreIdLiteral, LanguageIdLiteral, RulesetLiteral
from .base_model_extra import BaseModelExtra


RestrictionType = Literal[
    "rate_limit", "cooldown", "blacklist",
    "beatmap_duration", "beatmap_star_rating", "beatmap_ar_range",
    "beatmap_od_range", "beatmap_hp_range", "beatmap_cs_range",
    "beatmap_drain_range", "beatmap_bpm", "beatmap_genre",
    "beatmap_language", "beatmap_mode", "beatmap_difficulty_count",
    "beatmap_storyboard", "beatmap_video", "beatmap_tags",
    "beatmap_length", "composite",
    "never_ranked", "unique_artist_title",
]
RestrictionScope = Literal[
    "user",
    "beatmapset_type",
    "artist",
    "creator",
    "custom",
]


# ── Tier 1 configs ──────────────────────────────────────────────


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


# ── Tier 2 configs ──────────────────────────────────────────────


class DurationConfig(BaseModel):
    min_seconds: Optional[int] = None
    max_seconds: Optional[int] = None
    logic: Literal["max", "min", "all"] = "max"


class StarRatingConfig(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    logic: Literal["max", "min", "all", "any"] = "any"


class RangeConfig(BaseModel):
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


class BPMConfig(BaseModel):
    min_bpm: Optional[float] = None
    max_bpm: Optional[float] = None
    logic: Literal["any", "all", "avg"] = "any"


class GenreConfig(BaseModel):
    genre_ids: list[GenreIdLiteral]
    logic: Literal["any", "all"] = "any"


class LanguageConfig(BaseModel):
    language_ids: list[LanguageIdLiteral]
    logic: Literal["any", "all"] = "any"


class ModeConfig(BaseModel):
    allowed_modes: list[RulesetLiteral]

    @field_validator("allowed_modes")
    @classmethod
    def validate_modes(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("allowed_modes must contain at least one mode")
        return v


class DifficultyCountConfig(BaseModel):
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


class StoryboardConfig(BaseModel):
    allowed: bool


class VideoConfig(BaseModel):
    allowed: bool


class TagsConfig(BaseModel):
    tag_ids: list[int]
    logic: Literal["any", "all"] = "any"


class LengthConfig(BaseModel):
    min_hit_length: Optional[int] = None
    max_hit_length: Optional[int] = None
    min_total_length: Optional[int] = None
    max_total_length: Optional[int] = None
    logic: Literal["any", "all"] = "any"


class CompositeConfig(BaseModel):
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


class NeverRankedConfig(BaseModel):
    ruleset: Literal["osu", "taiko", "fruits", "mania"] = "osu"
    normalize_versions: bool = True


class UniqueArtistTitleConfig(BaseModel):
    ruleset: Literal["osu", "taiko", "fruits", "mania"] = "osu"
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

RestrictionConfig = Tier1Config | Tier2Config | Tier3Config


# ── ORM / API schemas ───────────────────────────────────────────


class RestrictionSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    queue_id: int
    restriction_type: RestrictionType
    config: dict[str, Any] = {}
    is_active: Optional[bool] = None
    version: str = "1.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime]


class RestrictionCreateSchema(BaseModel):
    restriction_type: RestrictionType
    config: dict[str, Any]
    version: str = "1.0"

    @field_validator("config")
    @classmethod
    def validate_config_by_type(
        cls, v: dict[str, Any], info
    ) -> dict[str, Any]:
        restriction_type = info.data.get("restriction_type")
        if not restriction_type:
            return v

        _schema_map: dict[str, type[BaseModel]] = {
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

        schema_cls = _schema_map.get(restriction_type)
        if schema_cls:
            validated = schema_cls(**v)
            return validated.model_dump(exclude_none=True)
        return v


class RestrictionUpdateSchema(BaseModel):
    id: Optional[int] = None
    is_active: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    version: Optional[str] = None
