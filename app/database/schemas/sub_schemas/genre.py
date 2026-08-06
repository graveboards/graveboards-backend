"""Pydantic schema for a beatmap genre."""

from __future__ import annotations

from pydantic.main import BaseModel

from app.osu_api.literals import GenreIdLiteral, GenreNameLiteral


class GenreSchema(BaseModel):
    """Genre identifier and name for a beatmap."""

    id: GenreIdLiteral
    name: GenreNameLiteral
