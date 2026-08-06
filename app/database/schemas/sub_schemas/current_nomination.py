"""Pydantic schema for a current nomination."""

from __future__ import annotations

from pydantic.main import BaseModel


class CurrentNominationSchema(BaseModel):
    """Details of a nomination currently in progress for a beatmapset."""

    beatmapset_id: int
    rulesets: list[str] | None
    reset: bool
    user_id: int
