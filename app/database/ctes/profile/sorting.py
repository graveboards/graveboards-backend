from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot
from app.search.datastructures import SortingOption
from app.search.enums import Scope


def profile_sorting_cte_factory(
    scope: Scope,
    sorting_option: SortingOption
) -> CTE:
    """Build a profile-derived ranking CTE for the given scope.

    Projects a profile-level sorting field into the active scope and assigns a
    row_number per root entity according to the configured order.

    Args:
        scope:
            The search scope determining the root entity.
        sorting_option:
            Sorting configuration including field and order.

    Returns:
        A CTE yielding (id, target, rank) for profile-based ordering.
    """
    target = sorting_option.field.target
    sorting_order = sorting_option.order
    field_name = sorting_option.field.field_name

    match scope:
        case Scope.BEATMAPS:
            return (
                select(
                    BeatmapSnapshot.id.label("id"),
                    target.label("target"),
                    func.row_number().over(
                        partition_by=BeatmapSnapshot.id,
                        order_by=sorting_order.sort_func(target)
                    ).label("rank")
                )
                .select_from(BeatmapSnapshot)
                .join(BeatmapSnapshot.owner_profiles)  # TODO: Needs testing if this works without aggregation
                .distinct(BeatmapSnapshot.id)
                .cte(f"beatmap_profile_{field_name}_ranked_cte")
            )
        case Scope.BEATMAPSETS:
            return (
                select(
                    BeatmapsetSnapshot.id.label("id"),
                    target.label("target"),
                    func.row_number().over(
                        partition_by=BeatmapsetSnapshot.id,
                        order_by=sorting_order.sort_func(target)
                    ).label("rank")
                )
                .select_from(BeatmapsetSnapshot)
                .join(BeatmapsetSnapshot.user_profile)
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"beatmapset_profile_{field_name}_ranked_cte")
            )
        case Scope.QUEUES:
            return (
                select(
                    Queue.id.label("id"),
                    target.label("target"),
                    func.row_number().over(
                        partition_by=Queue.id,
                        order_by=sorting_order.sort_func(target)
                    ).label("rank")
                )
                .select_from(Queue)
                .join(Queue.user_profile)
                .distinct(Queue.id)
                .cte(f"queue_profile_{field_name}_ranked_cte")
            )
        case Scope.REQUESTS:
            return (
                select(
                    Request.id.label("id"),
                    target.label("target"),
                    func.row_number().over(
                        partition_by=Request.id,
                        order_by=sorting_order.sort_func(target)
                    ).label("rank")
                )
                .select_from(Request)
                .join(Request.user_profile)
                .distinct(Request.id)
                .cte(f"request_profile_{field_name}_ranked_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for profile sorting: {scope}")