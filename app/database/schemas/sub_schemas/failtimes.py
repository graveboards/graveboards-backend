from __future__ import annotations
from pydantic.main import BaseModel


class FailtimesSchema(BaseModel):
    exit: list[int] | None
    fail: list[int] | None
