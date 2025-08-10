from datetime import datetime
from typing import Optional, ClassVar

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra
from .beatmapset_snapshot import BeatmapsetSnapshotSchema


class BeatmapsetListingSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmapset_id: int
    beatmapset_snapshot_id: int
    updated_at: datetime

    beatmapset_snapshot: "BeatmapsetSnapshotSchema"

    FRONTEND_INCLUDE: ClassVar = {
        "beatmapset_snapshot": BeatmapsetSnapshotSchema.FRONTEND_INCLUDE
    }
