from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic.config import ConfigDict
from pydantic.fields import Field

from .base_model_extra import BaseModelExtra
from .sub_schemas import BeatmapOsuApiSchema

if TYPE_CHECKING:
    from .beatmap_tag import BeatmapTagSchema
    from .beatmapset_snapshot import BeatmapsetSnapshotSchema
    from .leaderboard import LeaderboardSchema
    from .profile import ProfileSchema
    from .sub_schemas.beatmap_osu_api_schema import Owner


class BeatmapSnapshotSchema(BeatmapOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int
    beatmap_id: int
    snapshot_number: int | None = None
    snapshot_date: datetime | None = None

    beatmapset_snapshots: list[BeatmapsetSnapshotSchema] = []
    beatmap_tags: list[BeatmapTagSchema] = []
    leaderboard: LeaderboardSchema | None = None
    owner_profiles: list[ProfileSchema] = []

    owners: list[Owner] | None = Field(exclude=True, default=None)
    top_tag_ids: list[dict[Literal["tag_id"], int]] | None = Field(exclude=True, default=None)


class BeatmapSnapshotCreateSchema(BeatmapOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    beatmap_id: int
    snapshot_number: int | None = None


class BeatmapSnapshotUpdateSchema(BeatmapOsuApiSchema, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    snapshot_number: int | None = None
