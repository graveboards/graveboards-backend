from sqlalchemy.sql import select

from app.database.models import BeatmapsetSnapshot

description_description_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        BeatmapsetSnapshot.description["description"].astext.label("target")
    )
    .cte("description_description_cte")
)
