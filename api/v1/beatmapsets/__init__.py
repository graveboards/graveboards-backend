import httpx
from connexion import request

from api.utils import prime_query_kwargs
from app.beatmap_manager import BeatmapManager
from app.database import PostgresqlDB
from app.database.schemas import BeatmapsetSchema
from app.redis import RedisClient
from app.security import role_authorization
from app.database.enums import RoleName
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
        changelog = await bm.archive(beatmapset_id)
    except httpx.HTTPStatusError as e:
        return e.response.json(), e.response.status_code

    if changelog["snapshotted_beatmapset"] or changelog["snapshotted_beatmaps"]:
        num_snapshotted_beatmaps = len(changelog["snapshotted_beatmaps"])
        changelog["message"] = f"Snapshotted {num_snapshotted_beatmaps} beatmaps"
        status_code = 201
    elif changelog["updated_beatmapset"] or changelog["updated_beatmaps"]:
        num_beatmaps = len(changelog["updated_beatmaps"])
        num_beatmapset_fields = len(changelog["updated_beatmapset"]) - 1 if changelog["updated_beatmapset"] else 0  # Subtract inherent beatmapset_id
        num_beatmap_fields = sum((len(fields) for fields in changelog["updated_beatmaps"])) - num_beatmaps  # Subtract inherent beatmap_id(s)
        changelog["message"] = (
            f"Updated {num_beatmapset_fields} field(s) in the beatmapset "
            f"and {num_beatmap_fields} field(s) "
            f"in {num_beatmaps} beatmap(s)"
        )
        status_code = 200
    else:
        changelog["message"] = "The beatmapset and its beatmaps are fully up-to-date"
        status_code = 200

    return changelog, status_code
