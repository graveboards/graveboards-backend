from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.models import BeatmapsetSnapshot, ModelClass
from app.database.schemas import BeatmapsetSnapshotSchema
from . import zip

_LOADING_OPTIONS = {
    "beatmapset_tags": False,
    "beatmap_snapshots": False,
    "user_profile": False
}


async def search(beatmapset_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    beatmapset_snapshots = await db.get_many(
        BeatmapsetSnapshot,
        beatmapset_id=beatmapset_id,
        **kwargs
    )
    beatmapset_snapshots_data = [
        BeatmapsetSnapshotSchema.model_validate(beatmapset_snapshot).model_dump(
            exclude={"beatmap_snapshots", "beatmapset_tags", "user_profile"}
        )
        for beatmapset_snapshot in beatmapset_snapshots
    ]

    return beatmapset_snapshots_data, 200


async def get(beatmapset_id: int, snapshot_number: int):
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmapset_snapshot = await db.get(
            BeatmapsetSnapshot,
            beatmapset_id=beatmapset_id,
            _order_by=BeatmapsetSnapshot.snapshot_number.desc(),
            _offset=offset,
            **kwargs,
        )
    else:
        beatmapset_snapshot = await db.get(
            BeatmapsetSnapshot,
            beatmapset_id=beatmapset_id,
            snapshot_number=snapshot_number,
            **kwargs
        )

    if not beatmapset_snapshot:
        return {"message": f"BeatmapsetSnapshot with beatmapset_id '{beatmapset_id}' and snapshot_number '{snapshot_number}' not found"}, 404

    beatmapset_snapshot_data = BeatmapsetSnapshotSchema.model_validate(beatmapset_snapshot).model_dump(
        exclude={"beatmap_snapshots", "beatmapset_tags", "user_profile"}
    )

    return beatmapset_snapshot_data, 200
