"""Pydantic schema for a user's all-time highest rank."""

from __future__ import annotations

from datetime import datetime

from pydantic.main import BaseModel


class RankHighestSchema(BaseModel):
    """Highest rank a user has achieved and when it was recorded."""

    rank: int
    updated_at: datetime
