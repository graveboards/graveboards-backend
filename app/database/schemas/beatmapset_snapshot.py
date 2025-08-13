from copy import copy
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING, ClassVar

from pydantic.config import ConfigDict
from pydantic.functional_validators import model_validator
from pydantic.fields import Field

from app.utils import combine_checksums
from .base_model_extra import BaseModelExtra
from .sub_schemas import BeatmapsetOsuApiSchema, BeatmapOsuApiSchema

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema
    from .beatmapset_tag import BeatmapsetTagSchema
    from .profile import ProfileSchema


class BeatmapsetSnapshotSchema(BeatmapsetOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmapset_id: int
    snapshot_number: Optional[int] = None
    snapshot_date: Optional[datetime] = None
    checksum: str
    verified: Optional[bool] = None

    beatmap_snapshots: list["BeatmapSnapshotSchema"] = []
    beatmapset_tags: list["BeatmapsetTagSchema"] = []
    user_profile: Optional["ProfileSchema"] = None

    beatmaps: Optional[list["BeatmapOsuApiSchema"]] = Field(exclude=True, default=None)
    user: dict[str, Any] = Field(exclude=True, default=None)

    @model_validator(mode="before")
    @classmethod
    def from_osu_api_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_copy = copy(data)
            data_copy["beatmapset_id"] = data_copy.pop("id")
            data_copy["checksum"] = combine_checksums([beatmap["checksum"] for beatmap in data_copy["beatmaps"]])

            return data_copy

        return data

    FRONTEND_INCLUDE: ClassVar = {
        "artist": True,
        "artist_unicode": True,
        "beatmapset_id": True,
        "beatmap_snapshots": {
            "__all__": {"difficulty_rating", "total_length", "version"}
        },
        "covers": {"cover"},
        "creator": True,
        "preview_url": True,
        "title": True,
        "title_unicode": True,
        "user_profile": {"user_id", "avatar_url", "username"},
        "verified": True
    }
