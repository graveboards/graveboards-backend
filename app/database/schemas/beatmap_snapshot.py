from copy import copy
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.functional_validators import model_validator
from pydantic.fields import Field

from .base_model_extra import BaseModelExtra
from .sub_schemas import BeatmapOsuApiSchema

if TYPE_CHECKING:
    from .beatmapset_snapshot import BeatmapsetSnapshotSchema
    from .leaderboard import LeaderboardSchema
    from .profile import ProfileSchema
    from .beatmap_tag import BeatmapTagSchema


class BeatmapSnapshotSchema(BeatmapOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmap_id: int
    snapshot_number: Optional[int] = None
    snapshot_date: Optional[datetime] = None

    beatmapset_snapshots: list["BeatmapsetSnapshotSchema"] = []
    beatmap_tags: list["BeatmapTagSchema"] = []
    leaderboard: Optional["LeaderboardSchema"] = None
    owner_profiles: list["ProfileSchema"] = []

    owners: Optional[list[dict[str, Any]]] = Field(exclude=True, default=None)
    top_tag_ids: Optional[list[dict[str, int]]] = Field(exclude=True, default=None)

    @model_validator(mode="before")
    @classmethod
    def from_osu_api_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_copy = copy(data)

            if "beatmap_id" not in data_copy:
                data_copy["beatmap_id"] = data_copy.pop("id")

            return data_copy

        return data
