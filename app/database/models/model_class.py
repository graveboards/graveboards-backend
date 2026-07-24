from enum import Enum
from typing import Any
from typing import cast as typing_cast

from sqlalchemy.ext.hybrid import HybridExtensionType
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.sql.elements import ColumnElement

from .api_key import ApiKey
from .base import BaseType
from .beatmap import Beatmap
from .beatmap_listing import BeatmapListing
from .beatmap_snapshot import BeatmapSnapshot
from .beatmap_tag import BeatmapTag
from .beatmapset import Beatmapset
from .beatmapset_listing import BeatmapsetListing
from .beatmapset_snapshot import BeatmapsetSnapshot
from .beatmapset_tag import BeatmapsetTag
from .leaderboard import Leaderboard
from .oauth_token import OAuthToken
from .profile import Profile
from .profile_fetcher_task import ProfileFetcherTask
from .queue import Queue
from .queue_rule import QueueRule
from .request import Request
from .role import Role
from .score import Score
from .score_fetcher_task import ScoreFetcherTask
from .user import User


class ModelClass(Enum):
    USER = User
    ROLE = Role
    PROFILE = Profile
    API_KEY = ApiKey
    OAUTH_TOKEN = OAuthToken
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
    QUEUE_RULE = QueueRule

    @property
    def value(self) -> type[BaseType]:
        return typing_cast(type[BaseType], self._value_)

    @property
    def mapper(self) -> Mapper[BaseType]:
        return inspect(self.value)

    @property
    def required_columns(self) -> set[str]:
        required_columns = set()

        for column in self.mapper.columns:
            if (
                not column.primary_key
                and not column.nullable
                and column.default is None
                or column.primary_key
                and not column.autoincrement
            ):
                required_columns.add(column.name)

        return required_columns

    @property
    def column_names(self) -> set[str]:
        return {c.key for c in self.mapper.columns}

    @property
    def relationship_names(self) -> set[str]:
        return {r.key for r in self.mapper.relationships}

    @property
    def hybrid_property_names(self) -> set[str]:
        return {
            name
            for name, attr in self.mapper.all_orm_descriptors.items()
            if attr.extension_type in HybridExtensionType
        }

    @property
    def all_names(self) -> set[str]:
        return self.column_names | self.relationship_names | self.hybrid_property_names

    @property
    def primary_keys(self) -> tuple[ColumnElement[Any], ...]:
        return typing_cast(tuple[Any, ...], self.mapper.primary_key)
