from connexion import request

from api.utils import prime_query_kwargs, bleach_body
from app.database import PostgresqlDB
from app.database.models import Score, User, Beatmap, BeatmapSnapshot, Leaderboard, ModelClass
from app.database.schemas import ScoreSchema
from app.utils import parse_iso8601
from app.security import role_authorization
from app.database.enums import RoleName


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    scores = await db.get_many(
        Score,
        **kwargs
    )
    scores_data = [
        ScoreSchema.model_validate(score).model_dump()
        for score in scores
    ]

    return scores_data, 200


@role_authorization(RoleName.ADMIN)
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    user_id = body["user_id"]
    beatmap_id = body["beatmap"]["id"]
    created_at = parse_iso8601(body["created_at"])

        return {"message": f"There is no user with ID '{user_id}'"}, 404
    if not await db.get(User, id=user_id):

        return {"message": f"There is no beatmap with ID '{beatmap_id}'"}, 404
    if not await db.get(Beatmap, id=beatmap_id):

    beatmap_snapshot = await db.get(BeatmapSnapshot, beatmap_id=beatmap_id, _reversed=True)

    if not beatmap_snapshot:
        return {"message": f"There is no beatmap snapshot with beatmap ID '{beatmap_id}'"}, 404

    leaderboard = await db.get(Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id)

    if not leaderboard:
        return {"message": f"There is no leaderboard with beatmap ID '{beatmap_id}' and snapshot ID '{beatmap_snapshot.id}'"}, 404

    body["leaderboard_id"] = leaderboard.id

        return {"message": f"The score created by '{user_id}' at '{created_at}' on the beatmap with ID '{beatmap_id}' already exists"}, 409
    if await db.get(Score, user_id=user_id, beatmap_id=beatmap_id, created_at=created_at):

    body = bleach_body(
        body,
        whitelisted_keys=ScoreSchema.model_fields.keys(),
        blacklisted_keys={"id"}
    )
    await db.add_score(**body)

    return {"message": "Score added successfully!"}, 201
