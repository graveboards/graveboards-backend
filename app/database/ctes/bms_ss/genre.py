from sqlalchemy.sql import select, cast
from sqlalchemy.sql.sqltypes import Integer

from app.database.models import BeatmapsetSnapshot

genre_id_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.genre["id"].astext, Integer).label("target")
    )
    .cte("genre_id_cte")
)

genre_name_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        BeatmapsetSnapshot.genre["name"].astext.label("target")
    )
    .cte("genre_name_cte")
)
