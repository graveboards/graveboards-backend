from typing import Optional

from app.database.models import Score, Profile
from app.database.schemas import ScoreSchema, ProfileSchema
from tests.fixtures.osu import load_user_scores_best, load_user


def create_score_from_best(score_data: dict, user_id: Optional[int] = None, beatmap_id: Optional[int] = None, beatmapset_id: Optional[int] = None, leaderboard_id: int = 1) -> Score:
    """Create a Score model instance from osu! API score data."""
    schema_data = ScoreSchema.model_validate(score_data)
    return Score(
        id=score_data.get("id"),
        user_id=user_id or schema_data.user_id,
        beatmap_id=beatmap_id or schema_data.beatmap_id,
        beatmapset_id=beatmapset_id or schema_data.beatmapset_id,
        leaderboard_id=leaderboard_id,
        accuracy=schema_data.accuracy,
        created_at=schema_data.created_at,
        max_combo=schema_data.max_combo,
        mode=schema_data.mode,
        mode_int=schema_data.mode_int,
        mods=schema_data.mods,
        perfect=schema_data.perfect,
        pp=schema_data.pp,
        rank=schema_data.rank,
        score=schema_data.score,
        statistics=schema_data.statistics.model_dump() if hasattr(schema_data.statistics, "model_dump") else schema_data.statistics,
        type=schema_data.type,
    )


def create_score_from_user_best(user_id: int, index: int = 0, leaderboard_id: int = 1) -> Score:
    """Create a Score model from a user's best scores fixture."""
    scores_data = load_user_scores_best(f"scores_{user_id}_best")
    if index >= len(scores_data):
        raise ValueError(f"Index {index} out of range for user {user_id}")
    return create_score_from_best(scores_data[index], leaderboard_id=leaderboard_id)


def create_profile_from_user(user_data: dict) -> Profile:
    """Create a Profile model instance from osu! API user data."""
    schema_data = ProfileSchema.model_validate(user_data)
    profile_data = schema_data.model_dump(exclude_unset=True, exclude={"user_id"})
    
    return Profile(
        user_id=user_data.get("id"),
        **profile_data,
    )


def create_profile_from_user_id(user_id: int) -> Profile:
    """Create a Profile model from a user fixture."""
    user_data = load_user(f"mania/user_{user_id}_mania")
    return create_profile_from_user(user_data)
