from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, DateTime
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base

if TYPE_CHECKING:
    from .beatmapset_snapshot import BeatmapsetSnapshot


class BeatmapsetListing(Base):
    __tablename__ = "beatmapset_listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmapset_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapsets.id"), nullable=False, unique=True)
    beatmapset_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapset_snapshots.id"), nullable=False, unique=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)

    # Relationships
    beatmapset_snapshot: Mapped["BeatmapsetSnapshot"] = relationship(
        "BeatmapsetSnapshot",
        primaryjoin="BeatmapsetListing.beatmapset_snapshot_id == BeatmapsetSnapshot.id",
        uselist=False
    )
