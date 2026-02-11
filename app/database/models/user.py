from typing import TYPE_CHECKING

from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base
from .associations import user_role_association

if TYPE_CHECKING:
    from .profile import Profile
    from .role import Role
    from .score import Score
    from .api_key import ApiKey
    from .oauth_token import OAuthToken
    from .queue import Queue
    from .request import Request
    from .beatmapset import Beatmapset
    from .score_fetcher_task import ScoreFetcherTask
    from .profile_fetcher_task import ProfileFetcherTask


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_role_association,
        lazy=True
    )
    scores: Mapped[list["Score"]] = relationship(
        "Score",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    tokens: Mapped[list["OAuthToken"]] = relationship(
        "OAuthToken",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    queues: Mapped[list["Queue"]] = relationship(
        "Queue",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    requests: Mapped[list["Request"]] = relationship(
        "Request",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    beatmapsets: Mapped[list["Beatmapset"]] = relationship(
        "Beatmapset",
        lazy=True
    )
    score_fetcher_task: Mapped["ScoreFetcherTask"] = relationship(
        "ScoreFetcherTask",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    profile_fetcher_task: Mapped["ProfileFetcherTask"] = relationship(
        "ProfileFetcherTask",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
