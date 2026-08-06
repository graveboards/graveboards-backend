"""Pydantic schemas for profile fetcher tasks."""

from __future__ import annotations

from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class ProfileFetcherTaskSchema(BaseModel, BaseModelExtra):
    """Recurring profile fetch task with its last-fetch timestamp."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    enabled: bool = True
    last_fetch: datetime | None = None


class ProfileFetcherTaskCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a profile fetcher task."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    enabled: bool = True


class ProfileFetcherTaskUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing profile fetcher task."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    enabled: bool | None = None
    last_fetch: datetime | None = None
