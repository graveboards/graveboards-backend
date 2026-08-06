"""Pydantic schemas for beatmaps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema
    from .beatmapset import BeatmapsetSchema


class BeatmapSchema(BaseModel, BaseModelExtra):
    """Beatmap record with its beatmapset and snapshots."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    beatmapset_id: int

    beatmapset: BeatmapsetSchema | None = None
    snapshots: list[BeatmapSnapshotSchema] = []  # noqa: RUF012


class BeatmapCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a beatmap."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: int


class BeatmapUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing beatmap."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmapset_id: int | None = None
