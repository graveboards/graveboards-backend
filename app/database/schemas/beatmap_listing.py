"""Pydantic schemas for beatmap listings."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema


class BeatmapListingSchema(BaseModel, BaseModelExtra):
    """Beatmap listing record referencing its current snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    beatmap_id: int
    beatmap_snapshot_id: int
    updated_at: datetime

    beatmap_snapshot: BeatmapSnapshotSchema


class BeatmapListingCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a beatmap listing."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_id: int
    beatmap_snapshot_id: int


class BeatmapListingUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing beatmap listing."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_snapshot_id: int | None = None
