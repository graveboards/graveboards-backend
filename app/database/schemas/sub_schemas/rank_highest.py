from __future__ import annotations
from datetime import datetime

from pydantic.main import BaseModel


class RankHighestSchema(BaseModel):
    rank: int
    updated_at: datetime
