from __future__ import annotations
from copy import copy
from datetime import datetime
from typing import Any

from pydantic.config import ConfigDict
from pydantic.functional_validators import model_validator
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra
from .sub_schemas import ScoreStatisticsSchema


class ScoreSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    beatmap_id: int
    beatmapset_id: int
    leaderboard_id: int = 1
    accuracy: float
    created_at: datetime
    max_combo: int
    mode: str
    mode_int: int
    mods: list[str]
    perfect: bool
    pp: float | None = None
    rank: str
    score: int
    statistics: ScoreStatisticsSchema
    type: str

    @model_validator(mode="before")
    @classmethod
    def from_osu_api_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_copy = copy(data)
            data_copy.pop("id", None)
            data_copy["beatmap_id"] = data_copy["beatmap"]["id"]
            data_copy["beatmapset_id"] = data_copy["beatmapset"]["id"]

            return data_copy

        return data


class ScoreCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_id: int
    user_id: int
    accuracy: float
    max_combo: int
    mode: str
    mode_int: int
    mods: list[str]
    perfect: bool
    rank: str
    score: int
    statistics: ScoreStatisticsSchema
    type: str
    leaderboard_id: int | None = None
    pp: float | None = None


class ScoreUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    leaderboard_id: int | None = None
    accuracy: float | None = None
    max_combo: int | None = None
    mode: str | None = None
    mode_int: int | None = None
    mods: list[str] | None = None
    perfect: bool | None = None
    pp: float | None = None
    rank: str | None = None
    score: int | None = None
    statistics: ScoreStatisticsSchema | None = None
    type: str | None = None
