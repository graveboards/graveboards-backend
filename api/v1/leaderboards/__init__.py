from connexion import request

from api.utils import prime_query_kwargs
from app.database import PostgresqlDB
from app.database.schemas import LeaderboardSchema
from app.security import role_authorization
from app.enums import RoleName
from . import snapshots

_LOADING_OPTIONS = {
    "scores": False
}


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    leaderboards = await db.get_leaderboards(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    leaderboards_data = [
        LeaderboardSchema.model_validate(leaderboard).model_dump(
            exclude={"scores"}
        )
        for leaderboard in leaderboards
    ]

    return leaderboards_data, 200


async def get(beatmap_id: int):
    db: PostgresqlDB = request.state.db

    leaderboard = await db.get_leaderboard(
        beatmap_id=beatmap_id,
        _loading_options=_LOADING_OPTIONS,
        _reversed=True
    )

    if not leaderboard:
        return {"message": f"No Leaderboard found for beatmap_id '{beatmap_id}'"}, 404

    leaderboard_data = LeaderboardSchema.model_validate(leaderboard).model_dump(
        exclude={"scores"}
    )

    return leaderboard_data, 200


@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    beatmap_id = body["beatmap_id"]

    if not await db.get_beatmap(id=beatmap_id):
        return f"There is no beatmap with ID '{beatmap_id}'", 404

    beatmap_snapshot = await db.get_beatmap_snapshot(beatmap_id=beatmap_id, _reversed=True)

    if await db.get_leaderboard(beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id):
        return {"message": f"The leaderboard for the beatmap snapshot with ID '{beatmap_id}' and snapshot number '{beatmap_snapshot.snapshot_number}' already exists"}, 409

    await db.add_leaderboard(beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id)

    return {"message": "Leaderboard added successfully!"}, 201
