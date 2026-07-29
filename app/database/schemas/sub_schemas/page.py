from __future__ import annotations
from pydantic.main import BaseModel


class PageSchema(BaseModel):
    html: str
    raw: str
