from copy import copy
from datetime import datetime
from typing import Optional, Any

from pydantic.main import BaseModel
from pydantic.config import ConfigDict
from pydantic.functional_validators import model_validator

from .base_model_extra import BaseModelExtra
from .sub_schemas import ScoreStatisticsSchema


class ScoreSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    beatmap_id: int
    beatmapset_id: int
    leaderboard_id: int
    accuracy: float
    created_at: datetime
    max_combo: int
    mode: str
    mode_int: int
    mods: list[str]
    perfect: bool
    pp: Optional[float] = None
    rank: str
    score: int
    statistics: "ScoreStatisticsSchema"
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
