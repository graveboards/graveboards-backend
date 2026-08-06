"""Public re-exports of the schema definitions for the database layer."""

from __future__ import annotations

from . import rule
from .api_key import ApiKeyCreateSchema, ApiKeySchema, ApiKeyUpdateSchema
from .base_model_extra import BaseModelExtra
from .beatmap import BeatmapCreateSchema, BeatmapSchema, BeatmapUpdateSchema
from .beatmap_listing import (
    BeatmapListingCreateSchema,
    BeatmapListingSchema,
    BeatmapListingUpdateSchema,
)
from .beatmap_snapshot import (
    BeatmapSnapshotCreateSchema,
    BeatmapSnapshotSchema,
    BeatmapSnapshotUpdateSchema,
)
from .beatmap_tag import BeatmapTagCreateSchema, BeatmapTagSchema, BeatmapTagUpdateSchema
from .beatmapset import BeatmapsetCreateSchema, BeatmapsetSchema, BeatmapsetUpdateSchema
from .beatmapset_listing import (
    BeatmapsetListingCreateSchema,
    BeatmapsetListingSchema,
    BeatmapsetListingUpdateSchema,
)
from .beatmapset_snapshot import (
    BeatmapsetSnapshotCreateSchema,
    BeatmapsetSnapshotSchema,
    BeatmapsetSnapshotUpdateSchema,
)
from .beatmapset_tag import (
    BeatmapsetTagCreateSchema,
    BeatmapsetTagSchema,
    BeatmapsetTagUpdateSchema,
)
from .leaderboard import LeaderboardCreateSchema, LeaderboardSchema, LeaderboardUpdateSchema
from .oauth_token import OAuthTokenCreateSchema, OAuthTokenSchema, OAuthTokenUpdateSchema
from .profile import ProfileCreateSchema, ProfileSchema, ProfileUpdateSchema
from .profile_fetcher_task import (
    ProfileFetcherTaskCreateSchema,
    ProfileFetcherTaskSchema,
    ProfileFetcherTaskUpdateSchema,
)
from .queue import QueueCreateSchema, QueueSchema, QueueUpdateSchema
from .request import RequestCreateSchema, RequestSchema, RequestUpdateSchema
from .role import RoleCreateSchema, RoleSchema, RoleUpdateSchema
from .rule import (
    BlacklistConfig,
    CooldownConfig,
    RateLimitConfig,
    RuleCreateSchema,
    RuleReplaceSchema,
    RuleSchema,
    RuleUpdateSchema,
)
from .score import ScoreCreateSchema, ScoreSchema, ScoreUpdateSchema
from .score_fetcher_task import (
    ScoreFetcherTaskCreateSchema,
    ScoreFetcherTaskSchema,
    ScoreFetcherTaskUpdateSchema,
)
from .sub_schemas import *
from .user import UserCreateSchema, UserSchema, UserUpdateSchema

__all__ = [
    "ApiKeyCreateSchema",
    "ApiKeySchema",
    "ApiKeyUpdateSchema",
    "BaseModelExtra",
    "BeatmapCreateSchema",
    "BeatmapListingCreateSchema",
    "BeatmapListingSchema",
    "BeatmapListingUpdateSchema",
    "BeatmapSchema",
    "BeatmapSnapshotCreateSchema",
    "BeatmapSnapshotSchema",
    "BeatmapSnapshotUpdateSchema",
    "BeatmapTagCreateSchema",
    "BeatmapTagSchema",
    "BeatmapTagUpdateSchema",
    "BeatmapUpdateSchema",
    "BeatmapsetCreateSchema",
    "BeatmapsetListingCreateSchema",
    "BeatmapsetListingSchema",
    "BeatmapsetListingUpdateSchema",
    "BeatmapsetSchema",
    "BeatmapsetSnapshotCreateSchema",
    "BeatmapsetSnapshotSchema",
    "BeatmapsetSnapshotUpdateSchema",
    "BeatmapsetTagCreateSchema",
    "BeatmapsetTagSchema",
    "BeatmapsetTagUpdateSchema",
    "BeatmapsetUpdateSchema",
    "BlacklistConfig",
    "CooldownConfig",
    "LeaderboardCreateSchema",
    "LeaderboardSchema",
    "LeaderboardUpdateSchema",
    "OAuthTokenCreateSchema",
    "OAuthTokenSchema",
    "OAuthTokenUpdateSchema",
    "ProfileCreateSchema",
    "ProfileFetcherTaskCreateSchema",
    "ProfileFetcherTaskSchema",
    "ProfileFetcherTaskUpdateSchema",
    "ProfileSchema",
    "ProfileUpdateSchema",
    "QueueCreateSchema",
    "QueueSchema",
    "QueueUpdateSchema",
    "RateLimitConfig",
    "RequestCreateSchema",
    "RequestSchema",
    "RequestUpdateSchema",
    "RoleCreateSchema",
    "RoleSchema",
    "RoleUpdateSchema",
    "RuleCreateSchema",
    "RuleReplaceSchema",
    "RuleSchema",
    "RuleUpdateSchema",
    "ScoreCreateSchema",
    "ScoreFetcherTaskCreateSchema",
    "ScoreFetcherTaskSchema",
    "ScoreFetcherTaskUpdateSchema",
    "ScoreSchema",
    "ScoreUpdateSchema",
    "UserCreateSchema",
    "UserSchema",
    "UserUpdateSchema",
    "rule",
]

UserSchema.model_rebuild()
UserCreateSchema.model_rebuild()
UserUpdateSchema.model_rebuild()
RoleSchema.model_rebuild()
RoleCreateSchema.model_rebuild()
RoleUpdateSchema.model_rebuild()
ProfileSchema.model_rebuild()
ProfileCreateSchema.model_rebuild()
ProfileUpdateSchema.model_rebuild()
ApiKeySchema.model_rebuild()
ApiKeyCreateSchema.model_rebuild()
ApiKeyUpdateSchema.model_rebuild()
OAuthTokenSchema.model_rebuild()
OAuthTokenCreateSchema.model_rebuild()
OAuthTokenUpdateSchema.model_rebuild()
ScoreFetcherTaskSchema.model_rebuild()
ScoreFetcherTaskCreateSchema.model_rebuild()
ScoreFetcherTaskUpdateSchema.model_rebuild()
ProfileFetcherTaskSchema.model_rebuild()
ProfileFetcherTaskCreateSchema.model_rebuild()
ProfileFetcherTaskUpdateSchema.model_rebuild()
BeatmapSchema.model_rebuild()
BeatmapCreateSchema.model_rebuild()
BeatmapUpdateSchema.model_rebuild()
BeatmapSnapshotSchema.model_rebuild()
BeatmapSnapshotCreateSchema.model_rebuild()
BeatmapSnapshotUpdateSchema.model_rebuild()
BeatmapListingSchema.model_rebuild()
BeatmapListingCreateSchema.model_rebuild()
BeatmapListingUpdateSchema.model_rebuild()
BeatmapsetSchema.model_rebuild()
BeatmapsetCreateSchema.model_rebuild()
BeatmapsetUpdateSchema.model_rebuild()
BeatmapsetSnapshotSchema.model_rebuild()
BeatmapsetSnapshotCreateSchema.model_rebuild()
BeatmapsetSnapshotUpdateSchema.model_rebuild()
BeatmapsetListingSchema.model_rebuild()
BeatmapsetListingCreateSchema.model_rebuild()
BeatmapsetListingUpdateSchema.model_rebuild()
LeaderboardSchema.model_rebuild()
LeaderboardCreateSchema.model_rebuild()
LeaderboardUpdateSchema.model_rebuild()
ScoreSchema.model_rebuild()
ScoreCreateSchema.model_rebuild()
ScoreUpdateSchema.model_rebuild()
QueueSchema.model_rebuild()
QueueCreateSchema.model_rebuild()
QueueUpdateSchema.model_rebuild()
RequestSchema.model_rebuild()
RequestCreateSchema.model_rebuild()
RequestUpdateSchema.model_rebuild()
BeatmapsetTagSchema.model_rebuild()
BeatmapsetTagCreateSchema.model_rebuild()
BeatmapsetTagUpdateSchema.model_rebuild()
BeatmapTagSchema.model_rebuild()
BeatmapTagCreateSchema.model_rebuild()
BeatmapTagUpdateSchema.model_rebuild()
RuleSchema.model_rebuild()
RuleCreateSchema.model_rebuild()
RuleReplaceSchema.model_rebuild()
RuleUpdateSchema.model_rebuild()
