from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar

from sqlalchemy.ext.hybrid import HybridExtensionType
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.sql.elements import ColumnElement

from .api_key import ApiKey
from .base import Base
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

__all__ = ["ModelClass"]


class _ModelClassMeta(type):
    """Metaclass enabling ``for model_class in ModelClass: ...``."""

    def __iter__(cls) -> Iterator[ModelClass[Any]]:
        return iter(ModelClass._members)


class ModelClass[M: Base](metaclass=_ModelClassMeta):
    """Typed handle to one of the app's mapped model classes.

    Each member is parameterized on its own concrete model, so
    ``ModelClass.USER.value`` is exactly ``type[User]`` and generic helpers taking a
    ``ModelClass[M]`` return ``M`` rather than ``Base``.

    Provides:
      - ``ModelClass.USER`` / ``ModelClass.QUEUE`` / ...  member access
      - ``for model_class in ModelClass: ...``            iteration
      - ``isinstance(x, ModelClass)``                     membership check
      - ``ModelClass.from_model(User)``                   reverse lookup
    """

    _members: ClassVar[list[ModelClass[Any]]] = []
    _by_model: ClassVar[dict[type[Base], ModelClass[Any]]] = {}

    USER: ClassVar[ModelClass[User]]
    ROLE: ClassVar[ModelClass[Role]]
    PROFILE: ClassVar[ModelClass[Profile]]
    API_KEY: ClassVar[ModelClass[ApiKey]]
    OAUTH_TOKEN: ClassVar[ModelClass[OAuthToken]]
    SCORE_FETCHER_TASK: ClassVar[ModelClass[ScoreFetcherTask]]
    PROFILE_FETCHER_TASK: ClassVar[ModelClass[ProfileFetcherTask]]
    BEATMAP: ClassVar[ModelClass[Beatmap]]
    BEATMAP_SNAPSHOT: ClassVar[ModelClass[BeatmapSnapshot]]
    BEATMAP_LISTING: ClassVar[ModelClass[BeatmapListing]]
    BEATMAPSET: ClassVar[ModelClass[Beatmapset]]
    BEATMAPSET_SNAPSHOT: ClassVar[ModelClass[BeatmapsetSnapshot]]
    BEATMAPSET_LISTING: ClassVar[ModelClass[BeatmapsetListing]]
    LEADERBOARD: ClassVar[ModelClass[Leaderboard]]
    SCORE: ClassVar[ModelClass[Score]]
    QUEUE: ClassVar[ModelClass[Queue]]
    REQUEST: ClassVar[ModelClass[Request]]
    BEATMAPSET_TAG: ClassVar[ModelClass[BeatmapsetTag]]
    BEATMAP_TAG: ClassVar[ModelClass[BeatmapTag]]
    QUEUE_RULE: ClassVar[ModelClass[QueueRule]]

    def __init__(self, name: str, model: type[M]) -> None:
        self._name = name
        self._model = model
        ModelClass._by_model[model] = self
        ModelClass._members.append(self)

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> type[M]:
        return self._model

    @classmethod
    def from_model[T: Base](cls, model: type[T]) -> ModelClass[T]:
        """Reverse lookup by model class.

        Args:
            model:
                A SQLAlchemy model class registered with ``ModelClass``.

        Returns:
            The ``ModelClass`` wrapping ``model``, parameterized on ``model``'s own type.

        Raises:
            KeyError:
                If the model class is not registered with ``ModelClass``.
        """
        try:
            return cls._by_model[model]
        except KeyError:
            raise KeyError(f"{model.__name__} is not registered with ModelClass") from None

    @property
    def mapper(self) -> Mapper[M]:
        return inspect(self.value)

    @property
    def required_columns(self) -> set[str]:
        required: set[str] = set()

        for column in self.mapper.columns:
            if (
                not column.primary_key
                and not column.nullable
                and column.default is None
                or column.primary_key
                and not column.autoincrement
            ):
                required.add(column.name)

        return required

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
        return self.mapper.primary_key

    def __repr__(self) -> str:
        return f"ModelClass.{self._name}"


ModelClass.USER = ModelClass("USER", User)
ModelClass.ROLE = ModelClass("ROLE", Role)
ModelClass.PROFILE = ModelClass("PROFILE", Profile)
ModelClass.API_KEY = ModelClass("API_KEY", ApiKey)
ModelClass.OAUTH_TOKEN = ModelClass("OAUTH_TOKEN", OAuthToken)
ModelClass.SCORE_FETCHER_TASK = ModelClass("SCORE_FETCHER_TASK", ScoreFetcherTask)
ModelClass.PROFILE_FETCHER_TASK = ModelClass("PROFILE_FETCHER_TASK", ProfileFetcherTask)
ModelClass.BEATMAP = ModelClass("BEATMAP", Beatmap)
ModelClass.BEATMAP_SNAPSHOT = ModelClass("BEATMAP_SNAPSHOT", BeatmapSnapshot)
ModelClass.BEATMAP_LISTING = ModelClass("BEATMAP_LISTING", BeatmapListing)
ModelClass.BEATMAPSET = ModelClass("BEATMAPSET", Beatmapset)
ModelClass.BEATMAPSET_SNAPSHOT = ModelClass("BEATMAPSET_SNAPSHOT", BeatmapsetSnapshot)
ModelClass.BEATMAPSET_LISTING = ModelClass("BEATMAPSET_LISTING", BeatmapsetListing)
ModelClass.LEADERBOARD = ModelClass("LEADERBOARD", Leaderboard)
ModelClass.SCORE = ModelClass("SCORE", Score)
ModelClass.QUEUE = ModelClass("QUEUE", Queue)
ModelClass.REQUEST = ModelClass("REQUEST", Request)
ModelClass.BEATMAPSET_TAG = ModelClass("BEATMAPSET_TAG", BeatmapsetTag)
ModelClass.BEATMAP_TAG = ModelClass("BEATMAP_TAG", BeatmapTag)
ModelClass.QUEUE_RULE = ModelClass("QUEUE_RULE", QueueRule)
