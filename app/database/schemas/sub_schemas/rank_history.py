"""Pydantic schema for a user's rank history."""

from __future__ import annotations

from pydantic.main import BaseModel

from app.osu_api.literals import RulesetLiteral


class RankHistorySchema(BaseModel):
    """Rank data series for a ruleset."""

    mode: RulesetLiteral
    data: list[int]
