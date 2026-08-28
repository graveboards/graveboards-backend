"""Leaderboard endpoints for beatmap snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from connexion import request

from api.decorators import api_query, coerce_arguments
from api.utils import bleach_body, build_pydantic_include
from app.database.enums import RoleName

if TYPE_CHECKING:
    from api.http_types import APIResponse
    from app.database import PostgresqlDB
from app.database.models import BeatmapSnapshot, Leaderboard, ModelClass
from app.database.schemas import LeaderboardSchema
from app.exceptions import Conflict, NotFound
from app.security import role_authorization
from app.spec import get_include_schema

__all__ = ["patch", "post", "search"]


@api_query(ModelClass.LEADERBOARD)
@coerce_arguments(snapshot_number={"latest": -1})
async def search(beatmap_id: int, snapshot_number: int = -1, **_kwargs: Any) -> APIResponse:
    """Get the leaderboard for a beatmap snapshot.

    Returns:
        Tuple of (leaderboard data, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _sorting=[{"field": "BeatmapSnapshot.snapshot_number", "order": "desc"}],
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
        Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id, **_kwargs
    )

    if not leaderboard:
        raise NotFound(
            f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' has no leaderboard"
        )

    include = build_pydantic_include(
        obj=leaderboard,
        include_schema=get_include_schema(ModelClass.LEADERBOARD),
        request_include=_kwargs.get("_include"),
    )

    leaderboard_data = LeaderboardSchema.model_validate(leaderboard).model_dump(include=include)

    return leaderboard_data, 200, {"Content-Type": "application/json"}


@coerce_arguments(snapshot_number={"latest": -1})
@role_authorization(RoleName.ADMIN)
async def post(
    body: dict[str, Any],
    beatmap_id: int,
    snapshot_number: int = -1,
    **_kwargs: Any,
) -> APIResponse:
    """Create a new leaderboard for a beatmap snapshot.

    Returns:
        Tuple of (message, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _sorting=[{"field": "BeatmapSnapshot.snapshot_number", "order": "desc"}],
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

    if await db.get(Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id):
        raise Conflict(
            f"The leaderboard for the beatmap snapshot with ID '{beatmap_id}' and snapshot number '{beatmap_snapshot.snapshot_number}' already exists"
        )

    body = bleach_body(body, whitelisted_keys={"frozen"})

    await db.add(
        Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id, **body
    )

    return {"message": "Leaderboard added successfully!"}, 201, {"Content-Type": "application/json"}


@coerce_arguments(snapshot_number={"latest": -1})
@role_authorization(RoleName.ADMIN)
async def patch(
    body: dict[str, Any],
    beatmap_id: int,
    snapshot_number: int = -1,
    **_kwargs: Any,
) -> APIResponse:
    """Update an existing leaderboard for a beatmap snapshot.

    Returns:
        Tuple of (message, status code, headers).
    """
    db: PostgresqlDB = request.state.db

    if snapshot_number < 0:
        offset = abs(snapshot_number) - 1

        beatmap_snapshot = await db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _sorting=[{"field": "BeatmapSnapshot.snapshot_number", "order": "desc"}],
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
        Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=beatmap_snapshot.id
    )

    if not leaderboard:
        raise NotFound(
            f"BeatmapSnapshot with beatmap_id '{beatmap_id}' and snapshot_number '{snapshot_number}' has no leaderboard"
        )

    body = bleach_body(body, whitelisted_keys={"frozen"})

    delta = {key: value for key, value in body.items() if value != getattr(leaderboard, key)}

    await db.update(Leaderboard, leaderboard.id, **delta)

    return (
        {"message": "Leaderboard updated successfully!"},
        200,
        {"Content-Type": "application/json"},
    )
