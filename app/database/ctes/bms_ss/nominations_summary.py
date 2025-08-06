from sqlalchemy.sql import select, cast
from sqlalchemy.sql.sqltypes import Integer

from app.database.models import BeatmapsetSnapshot

nominations_summary_current_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.nominations_summary["current"].astext, Integer).label("target")
    )
    .cte("nominations_summary_current_cte")
)

nominations_summary_required_meta_main_ruleset_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.nominations_summary["required_meta"]["main_ruleset"].astext, Integer).label("target")
    )
    .cte("nominations_summary_required_meta_main_ruleset_cte")
)

nominations_summary_required_meta_non_main_ruleset_cte = (
    select(
        BeatmapsetSnapshot.id.label("beatmapset_snapshot_id"),
        cast(BeatmapsetSnapshot.nominations_summary["required_meta"]["non_main_ruleset"].astext, Integer).label("target")
    )
    .cte("nominations_summary_required_meta_non_main_ruleset_cte")
)
