from typing import Optional

from pydantic.main import BaseModel


class ScoreStatisticsSchema(BaseModel):
    count_100: Optional[int]
    count_300: Optional[int]
    count_50: Optional[int]
    count_geki: Optional[int]
    count_katu: Optional[int]
    count_miss: Optional[int]
