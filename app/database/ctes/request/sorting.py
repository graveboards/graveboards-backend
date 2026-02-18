from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association
from app.search.enums import Scope
from app.search.datastructures import SortingOption


def request_sorting_cte_factory(
    scope: Scope,
    sorting_option: SortingOption
) -> CTE:
    """Build a request-derived ranking CTE for the given scope.

    Projects a request-level sorting field into the active scope and assigns a
    row_number per root entity according to the configured sort order.

    Args:
        scope:
            The search scope determining the root entity.
        sorting_option:
            Sorting configuration including field and order.

    Returns:
        A CTE yielding (id, target, rank) for request-based ordering.
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
                .join(
                    beatmap_snapshot_beatmapset_snapshot_association,
                    beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id == BeatmapSnapshot.id
                )
                .join(
                    BeatmapsetSnapshot,
                    BeatmapsetSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id
                )
                .join(
                    Request,
                    Request.beatmapset_id == BeatmapsetSnapshot.beatmapset_id
                )
                .distinct(BeatmapSnapshot.id)
                .cte(f"beatmap_request_{field_name}_ranked_cte")
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
                .join(
                    Request,
                    Request.beatmapset_id == BeatmapsetSnapshot.beatmapset_id
                )
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"beatmapset_request_{field_name}_ranked_cte")
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
                .join(Queue.requests)
                .distinct(Queue.id)
                .cte(f"queue_request_{field_name}_ranked_cte")
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
                .distinct(Request.id)
                .cte(f"request_request_{field_name}_ranked_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for request sorting: {scope}")
