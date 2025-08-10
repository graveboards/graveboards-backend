from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base
from .beatmapset_snapshot import BeatmapsetSnapshot

if TYPE_CHECKING:
    from .profile import Profile
    from .queue import Queue


class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    beatmapset_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapsets.id"), nullable=False)
    beatmapset_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapset_snapshots.id"), nullable=False)
    queue_id: Mapped[int] = mapped_column(Integer, ForeignKey("queues.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text)
    mv_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    status: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    beatmapset_snapshot: Mapped["BeatmapsetSnapshot"] = relationship(
        "BeatmapsetSnapshot",
        uselist=False,
        viewonly=True,
        lazy=True
    )
    user_profile: Mapped["Profile"] = relationship(
        "Profile",
        primaryjoin="foreign(Request.user_id) == remote(Profile.user_id)",
        uselist=False,
        overlaps="requests",
        lazy=True
    )
    queue: Mapped["Queue"] = relationship(
        "Queue",
        back_populates="requests",
        overlaps="requests",
        lazy=True
    )
