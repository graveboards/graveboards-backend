"""Pydantic schemas for requests."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from app.database.literals import RequestStatusIntLiteral

from .base_model_extra import BaseModelExtra
from .beatmapset_snapshot import BeatmapsetSnapshotSchema

if TYPE_CHECKING:
    from .profile import ProfileSchema
    from .queue import QueueSchema


class RequestSchema(BaseModel, BaseModelExtra):
    """Request record with its status and related snapshot and queue."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    beatmapset_id: int
    beatmapset_snapshot_id: int | None = None
    queue_id: int
    comment: str | None = None
    mv_checked: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: RequestStatusIntLiteral | None = None
    rejection_reason: str | None = None

    beatmapset_snapshot: BeatmapsetSnapshotSchema | None = None
    user_profile: ProfileSchema | None = None
    queue: QueueSchema | None = None


class RequestCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a request."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int
    beatmapset_id: int
    beatmapset_snapshot_id: int | None = None
    queue_id: int
    comment: str | None = None
    mv_checked: bool = False


class RequestUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing request."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_snapshot_id: int | None = None
    queue_id: int | None = None
    comment: str | None = None
    mv_checked: bool | None = None
    status: RequestStatusIntLiteral | None = None
