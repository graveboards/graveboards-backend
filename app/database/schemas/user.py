from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmapset import BeatmapsetSchema
    from .oauth_token import OAuthTokenSchema
    from .profile import ProfileSchema
    from .queue import QueueSchema
    from .request import RequestSchema
    from .role import RoleSchema
    from .score import ScoreSchema


class UserSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int

    profile: ProfileSchema | None = None
    roles: list[RoleSchema] = []
    scores: list[ScoreSchema] = []
    tokens: list[OAuthTokenSchema] = []
    queues: list[QueueSchema] = []
    requests: list[RequestSchema] = []
    beatmapsets: list[BeatmapsetSchema] = []


class UserCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    osu_id: int
    username: str


class UserUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    osu_id: int | None = None
    username: str | None = None
    model_config = ConfigDict(from_attributes=True)

    id: int

    profile: ProfileSchema | None = None
    roles: list[RoleSchema] = []
    scores: list[ScoreSchema] = []
    tokens: list[OAuthTokenSchema] = []
    queues: list[QueueSchema] = []
    requests: list[RequestSchema] = []
    beatmapsets: list[BeatmapsetSchema] = []
