import httpx
from connexion import request

from api.utils import prime_query_kwargs
from app.beatmap_manager import BeatmapManager
from app.database import PostgresqlDB
from app.database.schemas import BeatmapsetSchema
from app.redis import RedisClient
from app.security import role_authorization
from app.enums import RoleName
from . import listings, snapshots

_LOADING_OPTIONS = {
    "snapshots": False
}


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    beatmapsets = await db.get_beatmapsets(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    beatmapsets_data = [
        BeatmapsetSchema.model_validate(beatmapset).model_dump(
            exclude={"snapshots"}
        )
        for beatmapset in beatmapsets
    ]

    return beatmapsets_data, 200


@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    rc: RedisClient = request.state.rc
    db: PostgresqlDB = request.state.db

    beatmapset_id = body["beatmapset_id"]

    try:
        bm = BeatmapManager(rc, db)
        beatmap_ids = await bm.archive(beatmapset_id)
    except httpx.HTTPStatusError as e:
        return e.response.json(), e.response.status_code

    if beatmap_ids:
        response = []

        for beatmap_id in beatmap_ids:
            snapshot_number = (await db.get_beatmap_snapshot(beatmap_id=beatmap_id, _reversed=True)).snapshot_number

            response.append({
                "beatmap_id": beatmap_id,
                "snapshot_number": snapshot_number
            })

        return response, 201
    else:
        return {"message": "The latest versions of all the beatmaps in the beatmapset have already been downloaded, no further action is needed"}, 200
