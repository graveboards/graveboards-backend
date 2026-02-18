from typing import Any

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot, beatmap_snapshot_beatmapset_snapshot_association
from app.search.enums import Scope


def bms_ss_filtering_cte_factory(
    scope: Scope,
    target: InstrumentedAttribute | QueryableAttribute[Any]
) -> CTE:
    """Build a beatmapset-derived filtering CTE for the given scope.

    Projects a beatmapset-level field into the active scope, joining through
    associations when the root entity is beatmap-, queue-, or request-based.

    Args:
        scope:
            The search scope determining the root entity.
        target:
            BeatmapsetSnapshot attribute to expose for filtering.

    Returns:
        A CTE yielding (id, target) aligned to the root scope.
    """
    field_name = target.key

    match scope:
        case Scope.BEATMAPS:
            return (
                select(
                    BeatmapSnapshot.id.label("id"),
                    target.label("target")
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
                .cte(f"beatmap_beatmapset_{field_name}_filter_cte")
            )
        case Scope.BEATMAPSETS:
            return (
                select(
                    BeatmapsetSnapshot.id.label("id"),
                    target.label("target")
                )
                .select_from(BeatmapsetSnapshot)
                .cte(f"beatmapset_beatmapset_{field_name}_filter_cte")
            )
        case Scope.QUEUES:
            return (
                select(
                    Queue.id.label("id"),
                    target.label("target")
                )
                .select_from(Queue)
                .join(Queue.requests)
                .join(Request.beatmapset_snapshot)
                .cte(f"queue_beatmapset_{field_name}_filter_cte")
            )
        case Scope.REQUESTS:
            return (
                select(
                    Request.id.label("id"),
                    target.label("target")
                )
                .select_from(Request)
                .join(Request.beatmapset_snapshot)
                .cte(f"request_beatmapset_{field_name}_filter_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for beatmapset filtering: {scope}")
