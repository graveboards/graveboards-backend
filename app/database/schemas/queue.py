"""Pydantic schemas for queues."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra
from .rule import RuleSchema

if TYPE_CHECKING:
    from .profile import ProfileSchema
    from .request import RequestSchema
    from .user import UserSchema


class QueueSchema(BaseModel, BaseModelExtra):
    """Queue record with its requests, managers, and rules."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_open: bool | None = None
    visibility: int | None = None
    enforce_user_id_match: bool | None = None

    requests: list[RequestSchema] = []  # noqa: RUF012
    managers: list[UserSchema] = []  # noqa: RUF012
    user_profile: ProfileSchema | None = None
    manager_profiles: list[ProfileSchema] = []  # noqa: RUF012
    rules: list[RuleSchema] = []  # noqa: RUF012


class QueueCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a queue."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    name: str
    description: str | None = None
    visibility: int | None = None
    enforce_user_id_match: bool | None = None


class QueueUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing queue."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int | None = None
    name: str | None = None
    description: str | None = None
    is_open: bool | None = None
    visibility: int | None = None
    enforce_user_id_match: bool | None = None
