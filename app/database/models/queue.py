"""Queue model representing a mapping submission queue."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String, Text

from app.utils import aware_utcnow

from .associations import queue_manager_association
from .base import Base

if TYPE_CHECKING:
    from .profile import Profile
    from .queue_rule import QueueRule
    from .request import Request
    from .user import User


class Queue(Base):
    """A mapping submission queue owned by a user."""

    __tablename__ = "queues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    visibility: Mapped[int] = mapped_column(Integer, default=0)
    enforce_user_id_match: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    requests: Mapped[list[Request]] = relationship(
        "Request",
        back_populates="queue",
        overlaps="queue",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )
    managers: Mapped[list[User]] = relationship(
        "User", secondary=queue_manager_association, backref="managed_queues", lazy=True
    )
    user_profile: Mapped[Profile] = relationship(
        "Profile",
        primaryjoin="foreign(Queue.user_id) == remote(Profile.user_id)",
        uselist=False,
        overlaps="queues",
        lazy=True,
    )
    manager_profiles: Mapped[list[Profile]] = relationship(
        "Profile",
        secondary=queue_manager_association,
        primaryjoin="Queue.id == queue_manager_association.c.queue_id",
        secondaryjoin="Profile.user_id == queue_manager_association.c.user_id",
        viewonly=True,
        lazy=True,
    )
    rules: Mapped[list[QueueRule]] = relationship(
        "QueueRule",
        back_populates="queue",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )

    __table_args__ = (UniqueConstraint("user_id", "name", name="_user_and_name_uc"),)
