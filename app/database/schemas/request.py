from datetime import datetime
from typing import Optional, TYPE_CHECKING, ClassVar

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from app.database.literals import RequestStatusIntLiteral
from .base_model_extra import BaseModelExtra
from .beatmapset_snapshot import BeatmapsetSnapshotSchema

if TYPE_CHECKING:
    from .profile import ProfileSchema
    from .queue import QueueSchema


class RequestSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    beatmapset_id: int
    beatmapset_snapshot_id: Optional[int] = None
    queue_id: int
    comment: Optional[str] = None
    mv_checked: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[RequestStatusIntLiteral] = None

    beatmapset_snapshot: Optional["BeatmapsetSnapshotSchema"] = None
    user_profile: Optional["ProfileSchema"] = None
    queue: Optional["QueueSchema"] = None

    FRONTEND_INCLUDE: ClassVar = {
        "id": True,
        "beatmapset_id": True,
        "user_id": True,
        "status": True,
        "comment": True,
        "beatmapset_snapshot": BeatmapsetSnapshotSchema.FRONTEND_INCLUDE,
        "user_profile": {"user_id", "avatar_url", "username"},
        "queue": {
            "name": True,
            "user_profile": {"user_id", "avatar_url", "username"},
            "manager_profiles": {
                "__all__": {"user_id", "avatar_url", "username"}
            }
        }
    }
