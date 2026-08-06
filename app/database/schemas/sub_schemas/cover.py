"""Pydantic schema for a profile cover image."""

from __future__ import annotations

from pydantic.main import BaseModel


class CoverSchema(BaseModel):
    """Cover image URLs and identifier for a user's profile."""

    custom_url: str | None
    url: str | None
    id: int | None
