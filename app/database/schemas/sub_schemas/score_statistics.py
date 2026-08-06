"""Pydantic schema for score hit statistics."""

from __future__ import annotations

from pydantic.main import BaseModel


class ScoreStatisticsSchema(BaseModel):
    """Hit result counts recorded for a score."""

    count_100: int | None
    count_300: int | None
    count_50: int | None
    count_geki: int | None
    count_katu: int | None
    count_miss: int | None
