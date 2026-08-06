"""Pydantic schema for a user's monthly playcount."""

from __future__ import annotations

from datetime import date

from pydantic.main import BaseModel


class UserMonthlyPlaycountSchema(BaseModel):
    """Number of plays a user made in a given month."""

    start_date: date
    count: int
