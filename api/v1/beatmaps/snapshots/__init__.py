from connexion import request

from api.decorators import api_query, coerce_arguments
from api.utils import build_pydantic_include
from app.spec import get_include_schema
from app.database import PostgresqlDB
from app.database.models import BeatmapSnapshot, ModelClass
from app.database.schemas import BeatmapSnapshotSchema
from . import osu



async def search(beatmap_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    beatmap_snapshots = await db.get_many(
        BeatmapSnapshot,
        beatmap_id=beatmap_id,
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

    return beatmap_snapshots_data, 200


async def get(beatmap_id: int, snapshot_number: int):
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset,
            **kwargs,
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            snapshot_number=snapshot_number,
            **kwargs
        )

    if not beatmap_snapshot:
        return {"message": f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' not found"}, 404

    include = build_pydantic_include(
        obj=beatmap_snapshot,
        include_schema=get_include_schema(ModelClass.BEATMAP_SNAPSHOT),
        request_include=kwargs.get("_include")
    )

    return beatmap_snapshot_data, 200
    beatmap_snapshot_data = BeatmapSnapshotSchema.model_validate(beatmap_snapshot).model_dump(include=include)

