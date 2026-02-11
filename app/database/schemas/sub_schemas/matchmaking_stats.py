from pydantic.main import BaseModel


class MatchmakingStatsSchema(BaseModel):
    first_placements: int
    is_rating_provisional: bool
    plays: int
    pool_id: int
    rank: int
    rating: int
    total_points: int
    user_id: int
    pool: "MatchmakingPoolSchema"


class MatchmakingPoolSchema(BaseModel):
    active: bool
    id: int
    name: str
    ruleset_id: int
    variant_id: int
