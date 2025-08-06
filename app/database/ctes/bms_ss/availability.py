from sqlalchemy.sql import select, cast
from sqlalchemy.sql.sqltypes import Boolean

from app.database.models import BeatmapsetSnapshot

availability_download_disabled_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.availability["download_disabled"].astext, Boolean).label("target")
    )
    .cte("availability_download_disabled_cte")
)

availability_more_information_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        BeatmapsetSnapshot.availability["more_information"].astext.label("target")
    )
    .cte("availability_more_information_cte")
)
