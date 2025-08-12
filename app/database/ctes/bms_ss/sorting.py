from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association
from app.search.datastructures import SortingOption
from app.search.enums import Scope


def bms_ss_sorting_cte_factory(scope: Scope, sorting_option: SortingOption) -> CTE:
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
                .distinct(BeatmapSnapshot.id)
                .cte(f"beatmap_beatmapset_{field_name}_ranked_cte")
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
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"beatmapset_beatmapset_{field_name}_ranked_cte")
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
                .distinct(Queue.id)
                .cte(f"queue_beatmapset_{field_name}_ranked_cte")
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
                .distinct(Request.id)
                .cte(f"request_beatmapset_{field_name}_ranked_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for beatmapset sorting: {scope}")