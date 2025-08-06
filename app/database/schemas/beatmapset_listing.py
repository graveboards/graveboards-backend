from datetime import datetime
from typing import Optional, TYPE_CHECKING, ClassVar

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmapset_snapshot import BeatmapsetSnapshotSchema


class BeatmapsetListingSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    beatmapset_id: int
    beatmapset_snapshot_id: int
    updated_at: datetime

    beatmapset_snapshot: "BeatmapsetSnapshotSchema"

    FRONTEND_INCLUDE: ClassVar = {
        "beatmapset_snapshot": {
            "artist": True,
            "artist_unicode": True,
            "beatmapset_id": True,
            "beatmap_snapshots": {
                "__all__": {"difficulty_rating", "total_length", "version"}
            },
            "covers": {"cover"},
            "creator": True,
            "preview_url": True,
            "title": True,
            "title_unicode": True,
            "user_id": True,
            "user_profile": {"avatar_url"},
            "verified": True
        }
    }
