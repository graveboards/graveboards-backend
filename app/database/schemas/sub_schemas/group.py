from typing import Optional

from pydantic.main import BaseModel


class GroupSchema(BaseModel):
    colour: Optional[str]
    has_listing: bool
    has_playmodes: bool
    id: int
    identifier: str
    is_probationary: bool
    name: str
    short_name: str
