"""Pydantic schema for a user group."""

from __future__ import annotations

from pydantic.main import BaseModel


class GroupSchema(BaseModel):
    """Core identity and display metadata for a user group."""

    colour: str | None
    has_listing: bool
    has_playmodes: bool
    id: int
    identifier: str
    is_probationary: bool
    name: str
    short_name: str
