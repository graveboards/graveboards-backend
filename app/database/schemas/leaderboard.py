from typing import Optional, TYPE_CHECKING
from datetime import datetime

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema
    from .score import ScoreSchema


class LeaderboardSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmap_id: int
    beatmap_snapshot_id: int
    created_at: datetime
    updated_at: datetime
    frozen: bool

    beatmap_snapshot: Optional["BeatmapSnapshotSchema"] = None
    scores: list["ScoreSchema"] = []
