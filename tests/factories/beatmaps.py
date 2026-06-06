from typing import Optional

from app.database.models import Beatmap
from tests.fixtures.osu import load_beatmap


def create_beatmap_from_api(beatmap_data: dict, beatmapset_id: Optional[int] = None, beatmap_user_id: Optional[int] = None) -> Beatmap:
    """Create a Beatmap model instance from osu! API beatmap data."""
    bs_id = beatmapset_id or beatmap_data.get("beatmapset_id")
    return Beatmap(
        id=beatmap_data.get("id"),
        beatmapset_id=bs_id,
    )


def create_beatmap_from_id(beatmap_id: int) -> Beatmap:
    """Create a Beatmap model from a beatmap fixture."""
    beatmap_data = load_beatmap(f"beatmap_{beatmap_id}")
    beatmapset_data = beatmap_data.get("beatmapset", {})
    bs_user_id = beatmapset_data.get("user_id")
    return create_beatmap_from_api(beatmap_data, beatmapset_id=None, beatmap_user_id=bs_user_id)
