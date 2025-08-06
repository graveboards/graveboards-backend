from sqlalchemy.sql import select, cast
from sqlalchemy.sql.sqltypes import Integer

from app.database.models import BeatmapsetSnapshot

language_id_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.language["id"].astext, Integer).label("target")
    )
    .cte("language_id_cte")
)

language_name_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        BeatmapsetSnapshot.language["name"].astext.label("target")
    )
    .cte("language_name_cte")
)
