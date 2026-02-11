from connexion import request

from api.decorators import api_query
from api.utils import bleach_body, build_pydantic_include
from app.database import PostgresqlDB
from app.database.models import Score, User, Beatmap, BeatmapSnapshot, Leaderboard, ModelClass
from app.database.schemas import ScoreSchema
from app.exceptions import NotFound, Conflict
from app.spec import get_include_schema
from app.utils import parse_iso8601
from app.security import role_authorization
from app.database.enums import RoleName


@api_query(ModelClass.SCORE, many=True)
async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    scores = await db.get_many(
        Score,
        **kwargs
    )

    if not scores:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=scores[0],
        include_schema=get_include_schema(ModelClass.SCORE),
        request_include=kwargs.get("_include")
    )

    scores_data = [
        ScoreSchema.model_validate(score).model_dump(include=include)
        for score in scores
    ]

    return scores_data, 200, {"Content-Type": "application/json"}


@api_query(ModelClass.SCORE)
async def get(score_id: int, **kwargs):
    db: PostgresqlDB = request.state.db

    score = await db.get(
        Score,
        id=score_id,
        **kwargs
    )

    if not score:
        raise NotFound(f"Score with ID '{score_id}' not found")

    include = build_pydantic_include(
        obj=score,
        include_schema=get_include_schema(ModelClass.SCORE),
        request_include=kwargs.get("_include")
    )

    score_data = ScoreSchema.model_validate(score).model_dump(include=include)

    return score_data, 200, {"Content-Type": "application/json"}


@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    user_id = body["user_id"]
    beatmap_id = body["beatmap"]["id"]
    created_at = parse_iso8601(body["created_at"])

    if not await db.get(User, id=user_id):
        raise NotFound(f"There is no user with ID '{user_id}'")

    if not await db.get(Beatmap, id=beatmap_id):
        raise NotFound(f"There is no beatmap with ID '{beatmap_id}'")

    beatmap_snapshot = await db.get(BeatmapSnapshot, beatmap_id=beatmap_id, _reversed=True)

    if not beatmap_snapshot:
        raise NotFound(f"There is no beatmap snapshot with beatmap ID '{beatmap_id}'")

    leaderboard = await db.get(Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id)

    if not leaderboard:
        raise NotFound(f"There is no leaderboard with beatmap ID '{beatmap_id}' and snapshot ID '{beatmap_snapshot.id}'")

    body["leaderboard_id"] = leaderboard.id

    if await db.get(Score, user_id=user_id, beatmap_id=beatmap_id, created_at=created_at):
        raise Conflict(f"The score created by '{user_id}' at '{created_at}' on the beatmap with ID '{beatmap_id}' already exists")

    body = bleach_body(
        body,
        whitelisted_keys=ScoreSchema.model_fields.keys(),
        blacklisted_keys={"id"}
    )
    await db.add(Score, **body)

    return {"message": "Score added successfully!"}, 201, {"Content-Type": "application/json"}
