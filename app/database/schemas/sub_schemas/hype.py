from __future__ import annotations
from pydantic.main import BaseModel


class HypeSchema(BaseModel):
    current: int
    required: int
