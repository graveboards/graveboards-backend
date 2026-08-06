"""Pydantic schema for a user team."""

from __future__ import annotations

from pydantic.main import BaseModel


class TeamSchema(BaseModel):
    """Identity and flag details for a user's team."""

    flag_url: str | None
    id: int
    name: str
    short_name: str
