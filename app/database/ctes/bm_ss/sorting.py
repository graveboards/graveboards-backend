from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association
from app.search.enums import Scope
from app.search.datastructures import SortingOption


def bm_ss_sorting_cte_factory(
    scope: Scope,
    sorting_option: SortingOption
) -> CTE:
    """Build a beatmap-derived ranking CTE for the given scope.

    Projects a beatmap-level sorting field into the active scope and assigns a
    deterministic row_number per root entity using the configured sort order.

    For parent scopes, joins traverse beatmap relationships before ranking.

    Args:
        scope:
            The search scope determining the root entity.
        sorting_option:
            Sorting configuration including field and order.

    Returns:
        A CTE yielding (id, target, rank) for downstream ordering.
    """
    target = sorting_option.field.target
    sorting_order = sorting_option.order
    field_name = target.key

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
                .distinct(BeatmapSnapshot.id)
                .cte(f"beatmap_beatmap_{field_name}_ranked_cte")
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
                    beatmap_snapshot_beatmapset_snapshot_association,
                    beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id == BeatmapsetSnapshot.id
                )
                .join(
                    BeatmapSnapshot,
                    BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
                )
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"beatmapset_beatmap_{field_name}_ranked_cte")
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
                .join(Request.beatmapset_snapshot)
                .join(
                    beatmap_snapshot_beatmapset_snapshot_association,
                    beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id == BeatmapsetSnapshot.id
                )
                .join(
                    BeatmapSnapshot,
                    BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
                )
                .distinct(Queue.id)
                .cte(f"queue_beatmap_{field_name}_ranked_cte")
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
                .join(Request.beatmapset_snapshot)
                .join(
                    beatmap_snapshot_beatmapset_snapshot_association,
                    beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id == BeatmapsetSnapshot.id
                )
                .join(
                    BeatmapSnapshot,
                    BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
                )
                .distinct(Request.id)
                .cte(f"request_beatmap_{field_name}_ranked_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for beatmap sorting: {scope}")
