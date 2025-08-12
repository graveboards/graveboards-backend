from typing import Iterable, Any

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association
from app.search.enums import Scope


def bm_ss_filtering_cte_factory(scope: Scope, target: InstrumentedAttribute | QueryableAttribute[Any], aggregated_conditions: Iterable[BinaryExpression] = None) -> CTE:
    if scope is not Scope.BEATMAPS and aggregated_conditions is None:
        raise ValueError(f"Scope {scope} must be supplied with aggregated_conditions")

    field_name = target.key

    match scope:
        case Scope.BEATMAPS:
            return (
                select(
                    BeatmapSnapshot.id.label("id"),
                    target.label("target")
                )
                .select_from(BeatmapSnapshot)
                .cte(f"beatmap_beatmap_{field_name}_filter_cte")
            )
        case Scope.BEATMAPSETS:
            return (
                select(
                    BeatmapsetSnapshot.id.label("id"),
                    func.array_agg(target).label("target")
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
                .group_by(BeatmapsetSnapshot.id)
                .having(*aggregated_conditions)
                .cte(f"beatmapset_beatmap_{field_name}_filter_cte")
            )
        case Scope.QUEUES:
            return (
                select(
                    Queue.id.label("id"),
                    func.array_agg(target).label("target")
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
                .group_by(Queue.id)
                .having(*aggregated_conditions)
                .cte(f"queue_beatmap_{field_name}_filter_cte")
            )
        case Scope.REQUESTS:
            return (
                select(
                    Request.id.label("id"),
                    func.array_agg(target).label("target")
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
                .group_by(Request.id)
                .having(*aggregated_conditions)
                .cte(f"request_beatmap_{field_name}_filter_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for beatmap filtering: {scope}")
