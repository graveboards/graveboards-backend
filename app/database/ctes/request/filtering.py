from typing import Any

from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute

from app.database.models import Request, BeatmapsetSnapshot


def request_filtering_cte_factory(target: InstrumentedAttribute | QueryableAttribute[Any]) -> CTE:
    field_name = target.key

    return (
        select(
            BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
            target.label("target")
        )
        .join(
            Request,
            Request.beatmapset_id == BeatmapsetSnapshot.beatmapset_id
        )
        .distinct(BeatmapsetSnapshot.id)
        .cte(f"request_{field_name}_filter_cte")
    )
