from typing import Optional

from app.database.models import Beatmap
from tests.fixtures.osu import load_beatmap


def create_beatmap_from_api(beatmap_data: dict, beatmapset_id: Optional[int] = None, beatmap_user_id: Optional[int] = None) -> Beatmap:
    """Create a Beatmap model instance from osu! API beatmap data."""
    bs_id = beatmapset_id or beatmap_data.get("beatmapset_id")
    beatmapset_user_id = beatmap_user_id or beatmap_data.get("user_id")
    return Beatmap(
        id=beatmap_data.get("id"),
        beatmapset_id=bs_id,
        difficulty_rating=beatmap_data.get("difficulty_rating"),
        mode=beatmap_data.get("mode"),
        status=beatmap_data.get("status"),
        total_length=beatmap_data.get("total_length"),
        user_id=beatmapset_user_id,
        version=beatmap_data.get("version"),
        accuracy=beatmap_data.get("accuracy"),
        ar=beatmap_data.get("ar"),
        bpm=beatmap_data.get("bpm"),
        convert=beatmap_data.get("convert"),
        count_circles=beatmap_data.get("count_circles"),
        count_sliders=beatmap_data.get("count_sliders"),
        count_spinners=beatmap_data.get("count_spinners"),
        cs=beatmap_data.get("cs"),
        deleted_at=beatmap_data.get("deleted_at"),
        drain=beatmap_data.get("drain"),
        hit_length=beatmap_data.get("hit_length"),
        is_scoreable=beatmap_data.get("is_scoreable"),
        last_updated=beatmap_data.get("last_updated"),
        mode_int=beatmap_data.get("mode_int"),
        passcount=beatmap_data.get("passcount"),
        playcount=beatmap_data.get("playcount"),
        ranked=beatmap_data.get("ranked"),
        url=beatmap_data.get("url"),
        checksum=beatmap_data.get("checksum"),
        failtimes=beatmap_data.get("failtimes"),
        max_combo=beatmap_data.get("max_combo"),
    )


def create_beatmap_from_id(beatmap_id: int) -> Beatmap:
    """Create a Beatmap model from a beatmap fixture."""
    beatmap_data = load_beatmap(f"beatmap_{beatmap_id}")
    beatmapset_data = beatmap_data.get("beatmapset", {})
    bs_user_id = beatmapset_data.get("user_id")
    return create_beatmap_from_api(beatmap_data, beatmapset_id=None, beatmap_user_id=bs_user_id)
