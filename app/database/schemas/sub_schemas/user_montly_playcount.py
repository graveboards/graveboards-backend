from datetime import date

from pydantic.main import BaseModel


class UserMonthlyPlaycountSchema(BaseModel):
    start_date: date
    count: int
