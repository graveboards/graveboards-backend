from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import BeatmapListing, BeatmapSnapshot, ModelClass
from app.database.schemas import BeatmapSnapshotSchema
from app.spec import get_include_schema


@api_query(ModelClass.BEATMAP_SNAPSHOT)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    beatmap_snapshots = await db.get_many(
        BeatmapSnapshot,
        _join=(BeatmapListing, BeatmapListing.beatmap_snapshot_id == BeatmapSnapshot.id),
        **kwargs
    )

    if not beatmap_snapshots:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmap_snapshots[0],
        include_schema=get_include_schema(ModelClass.BEATMAP_SNAPSHOT),
        request_include=kwargs.get("_include")
    )

    beatmap_snapshots_data = [
        BeatmapSnapshotSchema.model_validate(beatmap_snapshot).model_dump(include=include)
        for beatmap_snapshot in beatmap_snapshots
    ]

    return beatmap_snapshots_data, 200, {"Content-Type": "application/json"}
