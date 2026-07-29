from __future__ import annotations
from sqlalchemy.sql import select
from sqlalchemy.sql.functions import func

from app.database.models import BeatmapsetTag, beatmapset_tag_beatmapset_snapshot_association

beatmapset_tags_cte = (
    select(
        beatmapset_tag_beatmapset_snapshot_association.c.beatmapset_snapshot_id,
        func.string_agg(BeatmapsetTag.name, " ").label("target"),
    )
    .join(
        BeatmapsetTag,
        beatmapset_tag_beatmapset_snapshot_association.c.beatmapset_tag_id == BeatmapsetTag.id,
    )
    .group_by(beatmapset_tag_beatmapset_snapshot_association.c.beatmapset_snapshot_id)
    .cte("beatmapset_tags_cte")
)
