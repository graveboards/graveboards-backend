from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import Profile, BeatmapsetSnapshot, Request
from app.search.datastructures import SortingOption
from app.search.enums import Scope


def profile_sorting_cte_factory(sorting_option: SortingOption, scope: Scope) -> CTE:
    target = sorting_option.field.target
    sorting_order = sorting_option.order
    field_name = sorting_option.field.field_name

    base_query = (
        select(
            BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
            target.label("target"),
            func.row_number().over(
                partition_by=BeatmapsetSnapshot.id,
                order_by=sorting_order.sort_func(target)
            ).label("rank")
        )
    )

    match scope:
        case Scope.BEATMAPS:
            ...
        case Scope.BEATMAPSETS:
            return (
                base_query
                .select_from(BeatmapsetSnapshot)
                .join(
                    Profile,
                    Profile.user_id == BeatmapsetSnapshot.user_id
                )
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"beatmapset_profile_{field_name}_ranked_cte")
            )
        case Scope.QUEUES:
            ...
        case Scope.REQUESTS:
            return (
                base_query
                .select_from(BeatmapsetSnapshot)
                .join(
                    Request,
                    Request.beatmapset_id == BeatmapsetSnapshot.beatmapset_id
                )
                .join(Request.user_profile)
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"request_profile_{field_name}_ranked_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for profile filtering: {scope}")