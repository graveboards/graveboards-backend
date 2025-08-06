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
    from .oauth_token import OAuthToken
    from .queue import Queue
    from .request import Request
    from .beatmapset import Beatmapset


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", backref="user", uselist=False, lazy=True)
    roles: Mapped[list["Role"]] = relationship("Role", secondary=user_role_association, lazy=True)
    scores: Mapped[list["Score"]] = relationship("Score", lazy=True)
    tokens: Mapped[list["OAuthToken"]] = relationship("OAuthToken", lazy=True)
    queues: Mapped[list["Queue"]] = relationship("Queue", lazy=True)
    requests: Mapped[list["Request"]] = relationship("Request", lazy=True)
    beatmapsets: Mapped[list["Beatmapset"]] = relationship("Beatmapset", lazy=True)
