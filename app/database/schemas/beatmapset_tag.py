"""Pydantic schemas for beatmapset tags."""

from __future__ import annotations

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra


class BeatmapsetTagSchema(BaseModel, BaseModelExtra):
    """Beatmapset tag record."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str


class BeatmapsetTagCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a beatmapset tag."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str


class BeatmapsetTagUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing beatmapset tag."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str | None = None
