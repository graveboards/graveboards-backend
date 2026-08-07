"""Scores endpoints for beatmap snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from connexion import request

from api.decorators import api_query, coerce_arguments
from api.utils import build_pydantic_include
from app.database.models import BeatmapSnapshot, Leaderboard, ModelClass

if TYPE_CHECKING:
    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.schemas import ScoreSchema
from app.exceptions import NotFound
from app.spec import get_include_schema

__all__ = ["search"]


@api_query(ModelClass.SCORE, many=True)
@coerce_arguments(snapshot_number={"latest": -1})
async def search(beatmap_id: int, snapshot_number: int = -1, **kwargs: Any) -> APIResponse:
    """Search for scores on a beatmap snapshot.

    Returns:
        Tuple of (scores data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _order_by=BeatmapSnapshot.snapshot_number.desc(),
            _offset=offset,
        )
    else:
        beatmap_snapshot = await db.get(
            BeatmapSnapshot, beatmap_id=beatmap_id, snapshot_number=snapshot_number
        )

    if not beatmap_snapshot:
        raise NotFound(
            f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' not found"
        )

    snapshot_number = beatmap_snapshot.snapshot_number

    leaderboard = await db.get(
        Leaderboard,
        beatmap_id=beatmap_id,
        beatmap_snapshot_id=beatmap_snapshot.id,
        _include={"scores": True},
    )

    if not leaderboard:
        raise NotFound(
            f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' has no leaderboard"
        )

    if not leaderboard.scores:
        return [], 200, {"Content-Type": "application/json"}

    include = build_pydantic_include(
        obj=leaderboard.scores[0],
        include_schema=get_include_schema(ModelClass.SCORE),
        request_include=kwargs.get("_include"),
    )

    scores_data = [
        ScoreSchema.model_validate(score).model_dump(include=include)
        for score in leaderboard.scores
    ]

    return scores_data, 200, {"Content-Type": "application/json"}
