from typing import Iterable, Any

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from app.database.models import BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association


def bm_ss_filtering_cte_factory(target: InstrumentedAttribute | QueryableAttribute[Any], aggregated_conditions: Iterable[BinaryExpression]) -> CTE:
    field_name = target.key

    return (
        select(
            beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id,
            func.array_agg(target).label("target")
        )
        .join(
            BeatmapSnapshot,
            BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
        )
        .group_by(beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id)
        .having(*aggregated_conditions)
        .cte(f"beatmap_snapshot_{field_name}_filter_cte")
    )
