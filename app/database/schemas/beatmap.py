from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .leaderboard import LeaderboardSchema
    from .beatmap_snapshot import BeatmapSnapshotSchema


class BeatmapSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmapset_id: int

    leaderboards: list["LeaderboardSchema"] = []
    snapshots: list["BeatmapSnapshotSchema"] = []
