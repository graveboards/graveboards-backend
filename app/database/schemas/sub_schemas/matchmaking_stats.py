"""Pydantic schemas for matchmaking statistics."""

from __future__ import annotations

from pydantic.main import BaseModel


class MatchmakingStatsSchema(BaseModel):
    """Ranking and rating statistics for a user in a matchmaking pool."""

    first_placements: int
    is_rating_provisional: bool
    plays: int
    pool_id: int
    rank: int
    rating: int
    total_points: int
    user_id: int
    pool: MatchmakingPoolSchema


class MatchmakingPoolSchema(BaseModel):
    """Identity and ruleset details for a matchmaking pool."""

    active: bool
    id: int
    name: str
    ruleset_id: int
    variant_id: int
