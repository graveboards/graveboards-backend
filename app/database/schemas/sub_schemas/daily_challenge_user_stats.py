"""Pydantic schema for a user's daily challenge statistics."""

from __future__ import annotations

from datetime import datetime

from pydantic.main import BaseModel


class DailyChallengeUserStatsSchema(BaseModel):
    """Streaks and placements a user has earned in daily challenges."""

    daily_streak_best: int
    daily_streak_current: int
    last_update: datetime
    last_weekly_streak: datetime
    playcount: int
    top_10p_placements: int
    top_50p_placements: int
    user_id: int
    weekly_streak_best: int
    weekly_streak_current: int
