from sqlalchemy.sql import select, cast
from sqlalchemy.sql.sqltypes import Integer

from app.database.models import BeatmapsetSnapshot

hype_current_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.hype["current"].astext, Integer).label("target")
    )
    .cte("hype_current_cte")
)

hype_required_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.genre["required"].astext, Integer).label("target")
    )
    .cte("hype_required_cte")
)
