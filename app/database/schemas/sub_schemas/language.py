from __future__ import annotations
from pydantic.main import BaseModel

from app.osu_api.literals import LanguageIdLiteral, LanguageNameLiteral


class LanguageSchema(BaseModel):
    id: LanguageIdLiteral
    name: LanguageNameLiteral
