"""Pydantic schemas for beatmap tags."""

from __future__ import annotations

from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class BeatmapTagSchema(BaseModel, BaseModelExtra):
    """Beatmap tag record with its ruleset association."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ruleset_id: int | None
    description: str
    created_at: datetime
    updated_at: datetime


class BeatmapTagCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a beatmap tag."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str
    ruleset_id: int | None = None
    description: str


class BeatmapTagUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing beatmap tag."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str | None = None
    ruleset_id: int | None = None
    description: str | None = None
    updated_at: datetime | None = None
