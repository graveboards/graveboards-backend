from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap import BeatmapSchema
    from .beatmapset_snapshot import BeatmapsetSnapshotSchema


class BeatmapsetSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int

    beatmaps: list[BeatmapSchema] = []
    snapshots: list[BeatmapsetSnapshotSchema] = []


class BeatmapsetCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int


class BeatmapsetUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int | None = None
