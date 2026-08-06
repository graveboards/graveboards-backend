"""Pydantic schema for beatmap availability data."""

from __future__ import annotations

from pydantic.main import BaseModel


class AvailabilitySchema(BaseModel):
    """Beatmap download availability information for a beatmapset."""

    download_disabled: bool
    more_information: str | None
