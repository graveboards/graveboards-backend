from connexion import request

from api.decorators import api_query, coerce_arguments
from api.utils import bleach_body, build_pydantic_include
from app.database import PostgresqlDB
from app.database.enums import RoleName
from app.database.models import BeatmapSnapshot, ModelClass, Leaderboard
from app.database.schemas import LeaderboardSchema
from app.exceptions import NotFound, Conflict
from app.security import role_authorization
from app.spec import get_include_schema


@api_query(ModelClass.LEADERBOARD)
@coerce_arguments(snapshot_number={"latest": -1})
async def search(beatmap_id: int, snapshot_number: int = -1, **kwargs):
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            snapshot_number=snapshot_number
        )

    if not beatmap_snapshot:
        raise NotFound(f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' not found")

    snapshot_number = beatmap_snapshot.snapshot_number

    leaderboard = await db.get(
        Leaderboard,
        beatmap_id=beatmap_id,
        beatmap_snapshot_id=beatmap_snapshot.id,
        **kwargs
    )

    if not leaderboard:
        raise NotFound(f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' has no leaderboard")

    include = build_pydantic_include(
        obj=leaderboard,
        include_schema=get_include_schema(ModelClass.LEADERBOARD),
        request_include=kwargs.get("_include")
    )

    leaderboard_data = LeaderboardSchema.model_validate(leaderboard).model_dump(include=include)

    return leaderboard_data, 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN)
@coerce_arguments(snapshot_number={"latest": -1})
async def post(body: dict, beatmap_id: int, snapshot_number: int = -1, **kwargs):
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            snapshot_number=snapshot_number
        )

    if not beatmap_snapshot:
        raise NotFound(f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' not found")

    if await db.get(
            Leaderboard,
            beatmap_id=beatmap_id,
            beatmap_snapshot_id=beatmap_snapshot.id
    ):
        raise Conflict(f"The leaderboard for the beatmap snapshot with ID '{beatmap_id}' and snapshot number '{beatmap_snapshot.snapshot_number}' already exists")

    body = bleach_body(
        body,
        whitelisted_keys={"frozen"}
    )

    await db.add(
        Leaderboard,
        beatmap_id=beatmap_id,
        beatmap_snapshot_id=beatmap_snapshot.id,
        **body
    )

    return {"message": "Leaderboard added successfully!"}, 201, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN)
@coerce_arguments(snapshot_number={"latest": -1})
async def patch(body: dict, beatmap_id: int, snapshot_number: int = -1, **kwargs):
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            snapshot_number=snapshot_number
        )

    if not beatmap_snapshot:
        raise NotFound(f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' not found")

    snapshot_number = beatmap_snapshot.snapshot_number

    leaderboard = await db.get(
        Leaderboard,
        beatmap_id=beatmap_id,
        beatmap_snapshot_id=beatmap_snapshot.id
    )

    if not leaderboard:
        raise NotFound(f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' has no leaderboard")

    body = bleach_body(
        body,
        whitelisted_keys={"frozen"}
    )

    delta = {}

    for key, value in body.items():
        if value != getattr(leaderboard, key):
            delta[key] = value

    await db.update(Leaderboard, leaderboard.id, **delta)

    return {"message": "Leaderboard updated successfully!"}, 200, {"Content-Type": "application/json"}
