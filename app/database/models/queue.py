from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base
from .associations import queue_manager_association

if TYPE_CHECKING:
    from .request import Request
    from .user import User
    from .profile import Profile


class Queue(Base):
    __tablename__ = "queues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    visibility: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    requests: Mapped[list["Request"]] = relationship(
        "Request",
        back_populates="queue",
        overlaps="queue",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    managers: Mapped[list["User"]] = relationship(
        "User",
        secondary=queue_manager_association,
        backref="managed_queues",
        lazy=True
    )
    user_profile: Mapped["Profile"] = relationship(
        "Profile",
        primaryjoin="foreign(Queue.user_id) == remote(Profile.user_id)",
        uselist=False,
        overlaps="queues",
        lazy=True
    )
    manager_profiles: Mapped[list["Profile"]] = relationship(
        "Profile",
        secondary=queue_manager_association,
        primaryjoin="Queue.id == queue_manager_association.c.queue_id",
        secondaryjoin="Profile.user_id == queue_manager_association.c.user_id",
        viewonly=True,
        lazy=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="_user_and_name_uc"),
    )
