"""Pydantic schema for beatmap hype counts."""

from __future__ import annotations

from pydantic.main import BaseModel


class HypeSchema(BaseModel):
    """Current and required hype for a beatmapset."""

    current: int
    required: int
