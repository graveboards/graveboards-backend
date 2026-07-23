from sqlalchemy.sql import select
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association

bms_ss_with_multiple_bm_ss_cte = (
    select(
        beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id,
        func.count(beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id).label(
            "snapshot_count"
        ),
    )
    .join(
        BeatmapSnapshot,
        BeatmapSnapshot.id
        == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id,
    )
    .group_by(beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id)
    .having(func.count(beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id) > 1)
    .cte("count_cte")
)
