"""Pydantic schema for a user achievement."""

from __future__ import annotations

from datetime import datetime

from pydantic.main import BaseModel


class UserAchievementSchema(BaseModel):
    """Identifier and date for an achievement earned by a user."""

    achieved_at: datetime
    achievement_id: int
