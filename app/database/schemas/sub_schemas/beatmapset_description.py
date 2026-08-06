"""Pydantic schema for a beatmapset description."""

from __future__ import annotations

from pydantic.main import BaseModel


class BeatmapsetDescriptionSchema(BaseModel):
    """Schema for a beatmapset's description text."""

    description: str
