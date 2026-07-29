from __future__ import annotations
from pydantic.main import BaseModel


class CountrySchema(BaseModel):
    code: str
    name: str
