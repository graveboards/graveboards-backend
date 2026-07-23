from sqlalchemy.sql import select
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association

num_difficulties_cte = (
    select(
        beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id,
        func.count(BeatmapSnapshot.id).label("target"),
    )
    .join(
        beatmap_snapshot_beatmapset_snapshot_association,
        BeatmapSnapshot.id
        == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id,
    )
    .group_by(beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id)
    .cte("num_difficulties_cte")
)
