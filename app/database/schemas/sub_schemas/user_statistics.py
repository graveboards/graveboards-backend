from typing import Optional

from pydantic.main import BaseModel


class UserStatisticsSchema(BaseModel):
    count_100: int
    count_300: int
    count_50: int
    count_miss: int
    level: "LevelSchema"
    global_rank: Optional[int]
    global_rank_percent: Optional[float]
    global_rank_exp: Optional[int]
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
    grade_counts: "UserStatisticsGradeCountsSchema"
    country_rank: Optional[int]
    rank: "UserStatisticsRankSchema"


class LevelSchema(BaseModel):
    current: int
    progress: int


class UserStatisticsGradeCountsSchema(BaseModel):
    ss: int
    ssh: int
    s: int
    sh: int
    a: int


class UserStatisticsRankSchema(BaseModel):
    country: Optional[int]
