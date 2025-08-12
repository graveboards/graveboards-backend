from enum import Enum

from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.inspection import inspect

from .base import BaseType
from .user import User
from .role import Role
from .profile import Profile
from .api_key import ApiKey
from .oauth_token import OAuthToken
from .jwt import JWT
from .score_fetcher_task import ScoreFetcherTask
from .profile_fetcher_task import ProfileFetcherTask
from .beatmap import Beatmap
from .beatmap_snapshot import BeatmapSnapshot
from .beatmap_listing import BeatmapListing
from .beatmapset import Beatmapset
from .beatmapset_snapshot import BeatmapsetSnapshot
from .beatmapset_listing import BeatmapsetListing
from .leaderboard import Leaderboard
from .score import Score
from .queue import Queue
from .request import Request
from .beatmapset_tag import BeatmapsetTag
from .beatmap_tag import BeatmapTag


class ModelClass(Enum):
    USER = User
    ROLE = Role
    PROFILE = Profile
    API_KEY = ApiKey
    OAUTH_TOKEN = OAuthToken
    JWT = JWT
    SCORE_FETCHER_TASK = ScoreFetcherTask
    PROFILE_FETCHER_TASK = ProfileFetcherTask
    BEATMAP = Beatmap
    BEATMAP_SNAPSHOT = BeatmapSnapshot
    BEATMAP_LISTING = BeatmapListing
    BEATMAPSET = Beatmapset
    BEATMAPSET_SNAPSHOT = BeatmapsetSnapshot
    BEATMAPSET_LISTING = BeatmapsetListing
    LEADERBOARD = Leaderboard
    SCORE = Score
    QUEUE = Queue
    REQUEST = Request
    BEATMAPSET_TAG = BeatmapsetTag
    BEATMAP_TAG = BeatmapTag

    def get_required_columns(self) -> list[str]:
        required_columns = []

        for column in self.mapper.columns:
            if (
                not column.primary_key and not column.nullable and column.default is None
                or column.primary_key and not column.autoincrement
            ):
                required_columns.append(column.name)

        return required_columns

    @property
    def value(self) -> type[BaseType]:
        return self._value_

    @property
    def mapper(self) -> Mapper[BaseType]:
        return inspect(self.value)
