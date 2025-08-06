from datetime import date

from pydantic.main import BaseModel


class ReplayWatchedCountSchema(BaseModel):
    start_date: date
    count: int
