"""Pydantic schemas for score fetcher tasks."""

from __future__ import annotations

from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class ScoreFetcherTaskSchema(BaseModel, BaseModelExtra):
    """Recurring score fetch task with its last-fetch timestamp."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    enabled: bool = False
    last_fetch: datetime | None = None


class ScoreFetcherTaskCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a score fetcher task."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    enabled: bool = False


class ScoreFetcherTaskUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing score fetcher task."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    enabled: bool | None = None
    last_fetch: datetime | None = None
