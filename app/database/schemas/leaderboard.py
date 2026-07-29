from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic.config import ConfigDict
from pydantic.main import BaseModel

from .base_model_extra import BaseModelExtra

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshotSchema
    from .score import ScoreSchema


class LeaderboardSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    beatmap_id: int
    beatmap_snapshot_id: int
    created_at: datetime
    updated_at: datetime
    frozen: bool

    beatmap_snapshot: BeatmapSnapshotSchema | None = None
    scores: list[ScoreSchema] = []


class LeaderboardCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_id: int
    beatmap_snapshot_id: int
    frozen: bool = False


class LeaderboardUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_snapshot_id: int | None = None
    frozen: bool | None = None
