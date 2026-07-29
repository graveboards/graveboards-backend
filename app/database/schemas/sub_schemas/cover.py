from __future__ import annotations
from pydantic.main import BaseModel


class CoverSchema(BaseModel):
    custom_url: str | None
    url: str | None
    id: int | None
