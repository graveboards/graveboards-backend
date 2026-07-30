from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic.config import ConfigDict
from pydantic.fields import Field

from .base_model_extra import BaseModelExtra
from .sub_schemas import BeatmapOsuApiSchema, BeatmapsetOsuApiSchema

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema
    from .beatmapset_tag import BeatmapsetTagSchema
    from .profile import ProfileSchema


class BeatmapsetSnapshotSchema(BeatmapsetOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int
    beatmapset_id: int
    snapshot_number: int | None = None
    snapshot_date: datetime | None = None
    checksum: str
    verified: bool | None = None

    beatmap_snapshots: list[BeatmapSnapshotSchema] = []
    beatmapset_tags: list[BeatmapsetTagSchema] = []
    user_profile: ProfileSchema | None = None

    beatmaps: list[BeatmapOsuApiSchema] | None = Field(exclude=True, default=None)
    user: dict[str, Any] = Field(exclude=True, default_factory=dict)


class BeatmapsetSnapshotCreateSchema(BeatmapsetOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: int
    snapshot_number: int | None = None
    checksum: str
    verified: bool | None = None


class BeatmapsetSnapshotUpdateSchema(BeatmapsetOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    snapshot_number: int | None = None
    checksum: str | None = None
    verified: bool | None = None
