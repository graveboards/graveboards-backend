from typing import Optional

from pydantic.main import BaseModel


class TeamSchema(BaseModel):
    flag_url: Optional[str]
    id: int
    name: str
    short_name: str
