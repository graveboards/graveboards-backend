
from app.database.models import Profile
from app.database.schemas import ProfileSchema
from tests.fixtures.osu import load_user


def create_profile_from_user(user_data: dict) -> Profile:
    """Create a Profile model instance from osu! API user data."""
    schema_data = ProfileSchema.model_validate(user_data)
    profile_data = schema_data.model_dump(exclude_unset=True, exclude={"user_id"})

    return Profile(
        user_id=user_data.get("id"),
        **profile_data,
    )


def create_profile_from_user_id(user_id: int, mode: str = "mania") -> Profile:
    """Create a Profile model from a user fixture."""
    user_data = load_user(f"{mode}/user_{user_id}_{mode}")
    return create_profile_from_user(user_data)


def create_profile_from_user_best(user_id: int, index: int = 0) -> Profile:
    """Create a Profile model from a user's best scores fixture (user data embedded in score)."""
    from tests.fixtures.osu import load_user_scores_best
    scores_data = load_user_scores_best(f"scores_{user_id}_best")
    if index >= len(scores_data):
        raise ValueError(f"Index {index} out of range for user {user_id}")

    score_data = scores_data[index]
    user_data = score_data.get("user", {})

    if not user_data:
        return create_profile_from_user_id(user_id)

    return create_profile_from_user(user_data)
