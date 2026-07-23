from datetime import datetime
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema


class BeatmapListingSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    beatmap_id: int
    beatmap_snapshot_id: int
    updated_at: datetime

    beatmap_snapshot: BeatmapSnapshotSchema


class BeatmapListingCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_id: int
    beatmap_snapshot_id: int


class BeatmapListingUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_snapshot_id: int | None = None
