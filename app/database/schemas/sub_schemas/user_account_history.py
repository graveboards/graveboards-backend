"""Pydantic schema for a user account history entry."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic.main import BaseModel


class UserAccountHistorySchema(BaseModel):
    """Record of an account action such as a note, restriction, or silence."""

    id: int
    timestamp: datetime
    length: int
    permanent: bool
    type: Literal["note", "restriction", "silence", "tournament_ban"]
    description: str | None
