from copy import copy
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

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


class BeatmapsetSnapshotCreateSchema(BeatmapsetOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: int
    snapshot_number: Optional[int] = None
    checksum: str
    verified: Optional[bool] = None


class BeatmapsetSnapshotUpdateSchema(BeatmapsetOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    snapshot_number: Optional[int] = None
    checksum: Optional[str] = None
    verified: Optional[bool] = None
