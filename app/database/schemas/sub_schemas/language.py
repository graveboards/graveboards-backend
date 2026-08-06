"""Pydantic schema for a beatmap language."""

from __future__ import annotations

from pydantic.main import BaseModel

from app.osu_api.literals import LanguageIdLiteral, LanguageNameLiteral


class LanguageSchema(BaseModel):
    """Language identifier and name for a beatmap."""

    id: LanguageIdLiteral
    name: LanguageNameLiteral
