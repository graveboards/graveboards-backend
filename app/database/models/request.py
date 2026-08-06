"""Request model representing a beatmapset submission to a queue."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, Text

from app.utils import aware_utcnow

from .base import Base

if TYPE_CHECKING:
    from .beatmapset_snapshot import BeatmapsetSnapshot
    from .profile import Profile
    from .queue import Queue


class Request(Base):
    """A submission of a beatmapset snapshot to a queue."""

    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    beatmapset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("beatmapsets.id", ondelete="CASCADE"), nullable=False
    )
    beatmapset_snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("beatmapset_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    queue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False
    )
    comment: Mapped[str] = mapped_column(Text)
    mv_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )
    status: Mapped[int] = mapped_column(Integer, default=0)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    beatmapset_snapshot: Mapped[BeatmapsetSnapshot] = relationship(
        "BeatmapsetSnapshot", uselist=False, viewonly=True, lazy=True
    )
    user_profile: Mapped[Profile] = relationship(
        "Profile",
        primaryjoin="foreign(Request.user_id) == remote(Profile.user_id)",
        uselist=False,
        overlaps="requests",
        lazy=True,
    )
    queue: Mapped[Queue] = relationship(
        "Queue", back_populates="requests", overlaps="requests", lazy=True
    )

    __table_args__ = (
        UniqueConstraint("beatmapset_id", "queue_id", name="_beatmapset_and_queue_uc"),
    )
