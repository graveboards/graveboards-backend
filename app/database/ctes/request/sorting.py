from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapsetSnapshot, Request
from app.search.datastructures import SortingOption


def request_sorting_cte_factory(sorting_option: SortingOption) -> CTE:
    target = sorting_option.field.target
    sorting_order = sorting_option.order
    field_name = sorting_option.field.field_name

    return (
        select(
            BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
            target.label("target"),
            func.row_number().over(
                partition_by=BeatmapsetSnapshot.id,
                order_by=sorting_order.sort_func(target)
            ).label("rank")
        )
        .join(
            Request,
            Request.beatmapset_id == BeatmapsetSnapshot.beatmapset_id
        )
        .cte(f"request_{field_name}_ranked_cte")
    )
