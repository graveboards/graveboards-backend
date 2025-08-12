from datetime import datetime
from typing import Optional, TYPE_CHECKING, ClassVar

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .request import RequestSchema
    from .user import UserSchema
    from .profile import ProfileSchema


class QueueSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_open: Optional[bool] = None
    visibility: Optional[int] = None

    requests: list["RequestSchema"] = []
    managers: list["UserSchema"] = []
    user_profile: Optional["ProfileSchema"] = None
    manager_profiles: list["ProfileSchema"] = []

    FRONTEND_INCLUDE: ClassVar = {
        "id": True,
        "user_id": True,
        "name": True,
        "description": True,
        "is_open": True,
        "visibility": True,
        "user_profile": {"user_id", "avatar_url", "username"},
        "manager_profiles": {
            "__all__": {"user_id", "avatar_url", "username"}
        }
    }
