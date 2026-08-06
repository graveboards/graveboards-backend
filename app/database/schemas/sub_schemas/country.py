"""Pydantic schema for a country."""

from __future__ import annotations

from pydantic.main import BaseModel


class CountrySchema(BaseModel):
    """Country code and name for a user's profile."""

    code: str
    name: str
