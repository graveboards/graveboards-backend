"""Pydantic schema for a user page."""

from __future__ import annotations

from pydantic.main import BaseModel


class PageSchema(BaseModel):
    """Raw and HTML rendering of a user's profile page."""

    html: str
    raw: str
