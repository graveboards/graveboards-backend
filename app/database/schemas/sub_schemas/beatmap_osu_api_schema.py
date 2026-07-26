from copy import copy
from datetime import datetime
from typing import Any, ClassVar, Literal, TypedDict

from pydantic.functional_validators import field_validator, model_validator
from pydantic.main import BaseModel

from app.osu_api.literals import (
    RankedIntLiteral,
    RankedStatusLiteral,
    RulesetIntLiteral,
    RulesetLiteral,
)

from .failtimes import FailtimesSchema


class BeatmapOsuApiSchema(BaseModel):
    accuracy: float
    ar: float
    beatmapset_id: int
    bpm: float
    checksum: str
    count_circles: int
    count_sliders: int
    count_spinners: int
    cs: float
    deleted_at: datetime | None
    difficulty_rating: float
    drain: float
    failtimes: FailtimesSchema
    hit_length: int
    id: int
    is_scoreable: bool
    last_updated: datetime
    max_combo: int
    mode: RulesetLiteral
    mode_int: RulesetIntLiteral
    owners: list[Owner] | None = None
    passcount: int
    playcount: int
    ranked: RankedIntLiteral
    status: RankedStatusLiteral
    top_tag_ids: list[dict[Literal["tag_id"], int]] | None = None
    total_length: int
    url: str
    user_id: int
    version: str

    UPDATABLE_FIELDS: ClassVar[set[str]] = {
        "failtimes",
        "is_scoreable",
        "last_updated",
        "owners",
        "passcount",
        "playcount",
        "ranked",
        "status",
        "top_tag_ids",
        "user_id",
    }

    @model_validator(mode="before")
    @classmethod
    def from_snapshot(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        data_copy = copy(data)

        if hasattr(data_copy, "beatmap_id"):
            data_copy.id = data_copy.beatmap_id

        if hasattr(data_copy, "owner_profiles"):
            data_copy.owners = [
                {"id": owner.user_id, "username": owner.username}
                for owner in data_copy.owner_profiles
            ]

        if hasattr(data_copy, "beatmap_tags"):
            data_copy.top_tag_ids = [{"tag_id": tag.id} for tag in data_copy.beatmap_tags]

        return data_copy

    @field_validator("top_tag_ids", mode="before")
    @classmethod
    def filter_tag_keys(cls, value: Any) -> Any:
        if value is None:
            return None
        return [{"tag_id": item["tag_id"]} for item in value]


class Owner(TypedDict):
    id: int
    username: str
