from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapSnapshot, BeatmapsetSnapshot, beatmap_snapshot_beatmapset_snapshot_association
from app.search.datastructures import SortingOption


def bm_ss_sorting_cte_factory(sorting_option: SortingOption) -> CTE:
    target = sorting_option.field.target
    sorting_order = sorting_option.order
    field_name = target.key

    return (
        select(
            BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
            BeatmapSnapshot.id.label("beatmap_snapshot_id"),
            target.label("target"),
            func.row_number().over(
                partition_by=BeatmapsetSnapshot.id,
                order_by=sorting_order.sort_func(target)
            ).label("rank")
        )
        .join(
            beatmap_snapshot_beatmapset_snapshot_association,
            beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id == BeatmapSnapshot.id
        )
        .join(
            BeatmapsetSnapshot,
            BeatmapsetSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id
        )
        .cte(f"beatmap_snapshot_{field_name}_ranked_cte")
    )
