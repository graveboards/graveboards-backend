from __future__ import annotations
from pydantic.main import BaseModel


class CurrentNominationSchema(BaseModel):
    beatmapset_id: int
    rulesets: list[str] | None
    reset: bool
    user_id: int
