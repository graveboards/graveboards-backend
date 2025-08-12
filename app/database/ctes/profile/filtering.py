from typing import Any

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from app.database.models import BeatmapsetSnapshot, Request, Queue, BeatmapSnapshot
from app.search.enums import Scope


def profile_filtering_cte_factory(scope: Scope, target: InstrumentedAttribute | QueryableAttribute[Any]) -> CTE:
    field_name = target.key

    match scope:
        case Scope.BEATMAPS:
            return (
                select(
                    BeatmapSnapshot.id.label("id"),
                    target.label("target")
                )
                .select_from(BeatmapSnapshot)
                .join(BeatmapSnapshot.owner_profiles)  # TODO: Needs testing if this works without aggregation
                .cte(f"beatmap_profile_{field_name}_filter_cte")
            )
        case Scope.BEATMAPSETS:
            return (
                select(
                    BeatmapsetSnapshot.id.label("id"),
                    target.label("target")
                )
                .select_from(BeatmapsetSnapshot)
                .join(BeatmapsetSnapshot.user_profile)
                .cte(f"beatmapset_profile_{field_name}_filter_cte")
            )
        case Scope.QUEUES:
            return (
                select(
                    Queue.id.label("id"),
                    target.label("target")
                )
                .select_from(Queue)
                .join(Queue.user_profile)
                .cte(f"queue_profile_{field_name}_filter_cte")
            )
        case Scope.REQUESTS:
            return (
                select(
                    Request.id.label("id"),
                    target.label("target")
                )
                .select_from(Request)
                .join(Request.user_profile)
                .cte(f"request_profile_{field_name}_filter_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for profile filtering: {scope}")
