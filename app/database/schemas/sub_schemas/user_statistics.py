"""Pydantic schemas for a user's statistics."""

from __future__ import annotations

from pydantic.main import BaseModel


class UserStatisticsSchema(BaseModel):
    """Aggregated play statistics and ranks for a user."""

    count_100: int
    count_300: int
    count_50: int
    count_miss: int
    level: LevelSchema
    global_rank: int | None
    global_rank_percent: float | None
    global_rank_exp: int | None
    pp: float
    pp_exp: float
    ranked_score: int
    hit_accuracy: float
    play_count: int
    play_time: int
    total_score: int
    total_hits: int
    maximum_combo: int
    replays_watched_by_others: int
    is_ranked: bool
    grade_counts: UserStatisticsGradeCountsSchema
    country_rank: int | None
    rank: UserStatisticsRankSchema


class LevelSchema(BaseModel):
    """Current level and progress toward the next level."""

    current: int
    progress: int


class UserStatisticsGradeCountsSchema(BaseModel):
    """Grade counts a user has earned across beatmaps."""

    ss: int
    ssh: int
    s: int
    sh: int
    a: int


class UserStatisticsRankSchema(BaseModel):
    """Country rank for a user's statistics."""

    country: int | None
