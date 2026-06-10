from .base_model_extra import BaseModelExtra
from .user import UserSchema, UserCreateSchema, UserUpdateSchema
from .role import RoleSchema, RoleCreateSchema, RoleUpdateSchema
from .profile import ProfileSchema, ProfileCreateSchema, ProfileUpdateSchema
from .api_key import ApiKeySchema, ApiKeyCreateSchema, ApiKeyUpdateSchema
from .oauth_token import OAuthTokenSchema, OAuthTokenCreateSchema, OAuthTokenUpdateSchema
from .score_fetcher_task import ScoreFetcherTaskSchema, ScoreFetcherTaskCreateSchema, ScoreFetcherTaskUpdateSchema
from .profile_fetcher_task import ProfileFetcherTaskSchema, ProfileFetcherTaskCreateSchema, ProfileFetcherTaskUpdateSchema
from .beatmap import BeatmapSchema, BeatmapCreateSchema, BeatmapUpdateSchema
from .beatmap_snapshot import BeatmapSnapshotSchema, BeatmapSnapshotCreateSchema, BeatmapSnapshotUpdateSchema
from .beatmap_listing import BeatmapListingSchema, BeatmapListingCreateSchema, BeatmapListingUpdateSchema
from .beatmapset import BeatmapsetSchema, BeatmapsetCreateSchema, BeatmapsetUpdateSchema
from .beatmapset_snapshot import BeatmapsetSnapshotSchema, BeatmapsetSnapshotCreateSchema, BeatmapsetSnapshotUpdateSchema
from .beatmapset_listing import BeatmapsetListingSchema, BeatmapsetListingCreateSchema, BeatmapsetListingUpdateSchema
from .leaderboard import LeaderboardSchema, LeaderboardCreateSchema, LeaderboardUpdateSchema
from .score import ScoreSchema, ScoreCreateSchema, ScoreUpdateSchema
from .queue import QueueSchema, QueueCreateSchema, QueueUpdateSchema
from .request import RequestSchema, RequestCreateSchema, RequestUpdateSchema
from .beatmapset_tag import BeatmapsetTagSchema, BeatmapsetTagCreateSchema, BeatmapsetTagUpdateSchema
from .beatmap_tag import BeatmapTagSchema, BeatmapTagCreateSchema, BeatmapTagUpdateSchema
from .sub_schemas import *

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
