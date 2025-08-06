from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmapset_snapshot import BeatmapsetSnapshotSchema


class BeatmapsetSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int

    snapshots: list["BeatmapsetSnapshotSchema"] = []
