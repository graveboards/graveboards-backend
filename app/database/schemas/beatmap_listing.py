from datetime import datetime
from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema


class BeatmapListingSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmap_id: int
    beatmap_snapshot_id: int
    updated_at: datetime

    beatmap_snapshot: "BeatmapSnapshotSchema"
