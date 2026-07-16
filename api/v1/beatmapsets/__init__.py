import httpx
from connexion import request

from api.decorators import api_query
from api.utils import build_pydantic_include
from app.exceptions import NotFound
from app.spec import get_include_schema
from app.beatmaps import BeatmapManager
from app.database import PostgresqlDB
from app.database.models import Beatmapset, ModelClass
from app.database.schemas import BeatmapsetSchema
from app.redis import RedisClient
from app.security import role_authorization
from app.database.enums import RoleName
from . import listings, snapshots, tags


@api_query(ModelClass.BEATMAPSET, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    beatmapsets = await db.get_many(
        Beatmapset,
        **kwargs
    )

    if not beatmapsets:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=beatmapsets[0],
        include_schema=get_include_schema(ModelClass.BEATMAPSET),
        request_include=kwargs.get("_include")
    )

    beatmapsets_data = [
        BeatmapsetSchema.model_validate(beatmapset).model_dump(include=include)
        for beatmapset in beatmapsets
    ]

    return beatmapsets_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAPSET)
async def get(beatmapset_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    beatmapset = await db.get(
        Beatmapset,
        **kwargs
    )

    if not beatmapset:
        raise NotFound(f"Beatmapset with beatmapset_id '{beatmapset_id}' not found")

    include = build_pydantic_include(
        obj=beatmapset,
        include_schema=get_include_schema(ModelClass.BEATMAPSET),
        request_include=kwargs.get("_include")
    )

    beatmapset_data = BeatmapsetSchema.model_validate(beatmapset).model_dump(include=include)

    return beatmapset_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.BEATMAPSET)
@role_authorization(RoleName.ADMIN)
async def post(body: dict, rc: RedisClient = None, db: PostgresqlDB = None, bm: BeatmapManager = None, **kwargs):
    if rc is None:
        rc = request.state.rc
    if db is None:
        db = request.state.db

    beatmapset_id = body["id"]

    try:
        if bm is None:
            bm = BeatmapManager(rc, db)
        changelog = await bm.archive(beatmapset_id)
    except httpx.HTTPStatusError as e:
        return e.response.json(), e.response.status_code, {"Content-Type": "application/problem+json"}  # Inconsistent with other error formats, fix later

    if changelog.get("snapshotted_beatmapset") or changelog.get("snapshotted_beatmaps"):
        num_snapshotted_beatmaps = len(changelog.get("snapshotted_beatmaps", []))
        changelog["message"] = f"Snapshotted {num_snapshotted_beatmaps} beatmap(s)"
        if "updated_beatmapset" in changelog:
            del changelog["updated_beatmapset"]
        if "updated_beatmaps" in changelog:
            del changelog["updated_beatmaps"]
        status_code = 201
    elif changelog.get("updated_beatmapset") or changelog.get("updated_beatmaps"):
        num_beatmaps = len(changelog.get("updated_beatmaps", []))
        num_beatmapset_fields = len(changelog.get("updated_beatmapset", {})) - 1 if changelog.get("updated_beatmapset") else 0
        num_beatmap_fields = sum((len(fields) for fields in changelog.get("updated_beatmaps", []))) - num_beatmaps if num_beatmaps else 0
        changelog["message"] = (
            f"Updated {num_beatmapset_fields} field(s) in the beatmapset "
            f"and {num_beatmap_fields} field(s) "
            f"in {num_beatmaps} beatmap(s)"
        )
        if "snapshotted_beatmapset" in changelog:
            del changelog["snapshotted_beatmapset"]
        if "snapshotted_beatmaps" in changelog:
            del changelog["snapshotted_beatmaps"]
        status_code = 200
    else:
        changelog["message"] = "The beatmapset and its beatmaps are fully up-to-date"
        if "snapshotted_beatmapset" in changelog:
            del changelog["snapshotted_beatmapset"]
        if "snapshotted_beatmaps" in changelog:
            del changelog["snapshotted_beatmaps"]
        status_code = 200

    return changelog, status_code, {"Content-Type": "application/json"}
