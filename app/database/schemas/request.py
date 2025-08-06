from datetime import datetime
from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .profile import ProfileSchema
    from .queue import QueueSchema


class RequestSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    beatmapset_id: int
    queue_id: int
    comment: Optional[str] = None
    mv_checked: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[int] = None

    user_profile: Optional["ProfileSchema"] = None
    queue: Optional["QueueSchema"] = None
