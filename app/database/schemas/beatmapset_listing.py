"""Pydantic schemas for beatmapset listings."""

from __future__ import annotations

from datetime import datetime

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra
from .beatmapset_snapshot import BeatmapsetSnapshotSchema


class BeatmapsetListingSchema(BaseModel, BaseModelExtra):
    """Beatmapset listing record referencing its current snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    beatmapset_id: int
    beatmapset_snapshot_id: int
    updated_at: datetime

    beatmapset_snapshot: BeatmapsetSnapshotSchema


class BeatmapsetListingCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a beatmapset listing."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: int
    beatmapset_snapshot_id: int


class BeatmapsetListingUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing beatmapset listing."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_snapshot_id: int | None = None
