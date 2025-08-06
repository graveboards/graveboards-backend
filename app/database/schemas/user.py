from typing import Optional, TYPE_CHECKING

from pydantic.main import BaseModel
from pydantic.config import ConfigDict

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .profile import ProfileSchema
    from .role import RoleSchema
    from .score import ScoreSchema
    from .oauth_token import OAuthTokenSchema
    from .queue import QueueSchema
    from .request import RequestSchema
    from .beatmapset import BeatmapsetSchema


class UserSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int

    profile: Optional["ProfileSchema"] = None
    roles: list["RoleSchema"] = []
    scores: list["ScoreSchema"] = []
    tokens: list["OAuthTokenSchema"] = []
    queues: list["QueueSchema"] = []
    requests: list["RequestSchema"] = []
    beatmapsets: list["BeatmapsetSchema"] = []
