"""Pydantic schema for kudosu totals."""

from __future__ import annotations

from pydantic.main import BaseModel


class KudosuSchema(BaseModel):
    """Available and total kudosu for a user."""

    available: int
    total: int
