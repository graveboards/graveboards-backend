from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, DateTime, Boolean
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshot
    from .score import Score


class Leaderboard(Base):
    __tablename__ = "leaderboards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmaps.id"), nullable=False)
    beatmap_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmap_snapshots.id"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    beatmap_snapshot: Mapped["BeatmapSnapshot"] = relationship(
        "BeatmapSnapshot",
        back_populates="leaderboard",
        uselist=False,
        lazy=True
    )
    scores: Mapped[list["Score"]] = relationship(
        "Score",
        lazy=True
    )
