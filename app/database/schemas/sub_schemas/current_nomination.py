from typing import Optional

from pydantic.main import BaseModel


class CurrentNominationSchema(BaseModel):
    beatmapset_id: int
    rulesets: Optional[list[str]]
    reset: bool
    user_id: int
