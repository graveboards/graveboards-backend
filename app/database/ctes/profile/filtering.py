from typing import Any

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from app.database.models import BeatmapsetSnapshot, Request
from app.search.enums import Scope


def profile_filtering_cte_factory(target: InstrumentedAttribute | QueryableAttribute[Any], scope: Scope) -> CTE:
    field_name = target.key

    base_query = select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        target.label("target")
    )

    match scope:
        case Scope.BEATMAPS:
            ...
        case Scope.BEATMAPSETS:
            return (
                base_query
                .select_from(BeatmapsetSnapshot)
                .join(BeatmapsetSnapshot.user_profile)
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"beatmapset_profile_{field_name}_filter_cte")
            )
        case Scope.QUEUES:
            ...
        case Scope.REQUESTS:
            return (
                base_query
                .select_from(BeatmapsetSnapshot)
                .join(Request, Request.beatmapset_id == BeatmapsetSnapshot.beatmapset_id)
                .join(Request.user_profile)
                .distinct(BeatmapsetSnapshot.id)
                .cte(f"request_profile_{field_name}_filter_cte")
            )
        case _:
            raise ValueError(f"Unsupported scope for profile filtering: {scope}")
