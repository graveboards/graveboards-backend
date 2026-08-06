"""Pydantic schemas for beatmapsets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap import BeatmapSchema
    from .beatmapset_snapshot import BeatmapsetSnapshotSchema


class BeatmapsetSchema(BaseModel, BaseModelExtra):
    """Beatmapset record with its beatmaps and snapshots."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int

    beatmaps: list[BeatmapSchema] = []  # noqa: RUF012
    snapshots: list[BeatmapsetSnapshotSchema] = []  # noqa: RUF012


class BeatmapsetCreateSchema(BaseModel, BaseModelExtra):
    """Fields required to create a beatmapset."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int


class BeatmapsetUpdateSchema(BaseModel, BaseModelExtra):
    """Updatable fields for an existing beatmapset."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int | None = None
