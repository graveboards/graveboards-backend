from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, DateTime
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshot


class BeatmapListing(Base):
    __tablename__ = "beatmap_listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmaps.id"), nullable=False, unique=True)
    beatmap_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmap_snapshots.id"), nullable=False, unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)

    # Relationships
    beatmap_snapshot: Mapped["BeatmapSnapshot"] = relationship(
        "BeatmapSnapshot",
        primaryjoin="BeatmapListing.beatmap_snapshot_id == BeatmapSnapshot.id",
        uselist=False
    )
