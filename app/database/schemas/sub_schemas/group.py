from __future__ import annotations
from pydantic.main import BaseModel


class GroupSchema(BaseModel):
    colour: str | None
    has_listing: bool
    has_playmodes: bool
    id: int
    identifier: str
    is_probationary: bool
    name: str
    short_name: str
