from .base_model_extra import BaseModelExtra
from .user import UserSchema
from .role import RoleSchema
from .profile import ProfileSchema
from .api_key import ApiKeySchema
from .oauth_token import OAuthTokenSchema
from .jwt import JWTSchema
from .score_fetcher_task import ScoreFetcherTaskSchema
from .profile_fetcher_task import ProfileFetcherTaskSchema
from .beatmap import BeatmapSchema
from .beatmap_snapshot import BeatmapSnapshotSchema
from .beatmap_listing import BeatmapListingSchema
from .beatmapset import BeatmapsetSchema
from .beatmapset_snapshot import BeatmapsetSnapshotSchema
from .beatmapset_listing import BeatmapsetListingSchema
from .leaderboard import LeaderboardSchema
from .score import ScoreSchema
from .queue import QueueSchema
from .request import RequestSchema
from .beatmapset_tag import BeatmapsetTagSchema
from .beatmap_tag import BeatmapTagSchema
from .sub_schemas import *

UserSchema.model_rebuild()
RoleSchema.model_rebuild()
ProfileSchema.model_rebuild()
ApiKeySchema.model_rebuild()
OAuthTokenSchema.model_rebuild()
JWTSchema.model_rebuild()
ScoreFetcherTaskSchema.model_rebuild()
ProfileFetcherTaskSchema.model_rebuild()
BeatmapSchema.model_rebuild()
BeatmapSnapshotSchema.model_rebuild()
BeatmapListingSchema.model_rebuild()
BeatmapsetSchema.model_rebuild()
BeatmapsetSnapshotSchema.model_rebuild()
BeatmapsetListingSchema.model_rebuild()
LeaderboardSchema.model_rebuild()
ScoreSchema.model_rebuild()
QueueSchema.model_rebuild()
RequestSchema.model_rebuild()
BeatmapsetTagSchema.model_rebuild()
BeatmapTagSchema.model_rebuild()
