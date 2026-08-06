"""Pydantic schemas for users."""

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
    """User record with its profile and related entities."""

    model_config = ConfigDict(from_attributes=True)

    id: int

    profile: ProfileSchema | None = None
    roles: list[RoleSchema] = []  # noqa: RUF012
    scores: list[ScoreSchema] = []  # noqa: RUF012
    tokens: list[OAuthTokenSchema] = []  # noqa: RUF012
    queues: list[QueueSchema] = []  # noqa: RUF012
    requests: list[RequestSchema] = []  # noqa: RUF012
    beatmapsets: list[BeatmapsetSchema] = []  # noqa: RUF012


class UserCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a user."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    osu_id: int
    username: str


class UserUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing user."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    osu_id: int | None = None
    username: str | None = None

    id: int

    profile: ProfileSchema | None = None
    roles: list[RoleSchema] = []  # noqa: RUF012
    scores: list[ScoreSchema] = []  # noqa: RUF012
    tokens: list[OAuthTokenSchema] = []  # noqa: RUF012
    queues: list[QueueSchema] = []  # noqa: RUF012
    requests: list[RequestSchema] = []  # noqa: RUF012
    beatmapsets: list[BeatmapsetSchema] = []  # noqa: RUF012
