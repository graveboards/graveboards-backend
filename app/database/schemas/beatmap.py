from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmapset import BeatmapsetSchema
    from .beatmap_snapshot import BeatmapSnapshotSchema


class BeatmapSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmapset_id: int

    beatmapset: Optional[BeatmapsetSchema] = None
    snapshots: list["BeatmapSnapshotSchema"] = []


class BeatmapCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: int


class BeatmapUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: Optional[int] = None
