from typing import Optional

from app.database.models import Beatmapset
from tests.fixtures.osu import load_beatmapset


def create_beatmapset_from_api(beatmapset_data: dict, user_id: Optional[int] = None, beatmap_user_id: Optional[int] = None) -> Beatmapset:
    """Create a Beatmapset model instance from osu! API beatmapset data."""
    if user_id is None:
        user_id = beatmapset_data.get("user_id")
        if user_id is None and beatmap_user_id is not None:
            user_id = beatmap_user_id
    return Beatmapset(
        id=beatmapset_data.get("id"),
        user_id=user_id,
    )


def create_beatmapset_from_id(beatmapset_id: int, beatmap_user_id: Optional[int] = None) -> Beatmapset:
    """Create a Beatmapset model from a beatmapset fixture."""
    beatmapset_data = load_beatmapset(f"beatmapset_{beatmapset_id}")
    return create_beatmapset_from_api(beatmapset_data, beatmap_user_id=beatmap_user_id)

