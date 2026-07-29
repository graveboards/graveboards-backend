from __future__ import annotations
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import Float, Numeric

from app.database.ctes.bms_ss.bm_ss import bms_ss_with_multiple_bm_ss_cte
from app.database.models import BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association

hit_length_cte = (
    select(
        beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id,
        BeatmapSnapshot.hit_length.label("hit_length"),
    )
    .join(
        beatmap_snapshot_beatmapset_snapshot_association,
        BeatmapSnapshot.id
        == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id,
    )
    .join(
        bms_ss_with_multiple_bm_ss_cte,
        bms_ss_with_multiple_bm_ss_cte.c.beatmapset_snapshot_id
        == beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id,
    )
    .cte("hit_length_cte")
)

hit_length_agg_cte = (
    select(
        hit_length_cte.c.beatmapset_snapshot_id,
        func.array_agg(hit_length_cte.c.hit_length).label("hit_length_agg"),
    )
    .where(hit_length_cte.c.hit_length.isnot(None))
    .group_by(hit_length_cte.c.beatmapset_snapshot_id)
    .cte("hit_length_agg_cte")
)

min_hit_length_cte = (
    select(
        hit_length_cte.c.beatmapset_snapshot_id,
        func.min(hit_length_cte.c.hit_length).label("target"),
    )
    .group_by(hit_length_cte.c.beatmapset_snapshot_id)
    .cte("min_hit_length_cte")
)

max_hit_length_cte = (
    select(
        hit_length_cte.c.beatmapset_snapshot_id,
        func.max(hit_length_cte.c.hit_length).label("target"),
    )
    .group_by(hit_length_cte.c.beatmapset_snapshot_id)
    .cte("max_hit_length_cte")
)

avg_hit_length_cte = (
    select(
        hit_length_cte.c.beatmapset_snapshot_id,
        cast(func.round(cast(func.avg(hit_length_cte.c.hit_length), Numeric), 2), Float).label(
            "target"
        ),
    )
    .group_by(hit_length_cte.c.beatmapset_snapshot_id)
    .cte("avg_hit_length_cte")
)
