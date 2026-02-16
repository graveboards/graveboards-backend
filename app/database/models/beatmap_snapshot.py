from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.dialects.postgresql.json import JSONB

from app.utils import aware_utcnow
from .base import Base
from .associations import beatmap_snapshot_beatmapset_snapshot_association, beatmap_snapshot_owner_association, beatmap_tag_beatmap_snapshot_association
from .types import AwareDateTime

if TYPE_CHECKING:
    from .beatmapset_snapshot import BeatmapsetSnapshot
    from .leaderboard import Leaderboard
    from .profile import Profile
    from .beatmap_tag import BeatmapTag


class BeatmapSnapshot(Base):
    __tablename__ = "beatmap_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmaps.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    snapshot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(AwareDateTime(), default=aware_utcnow)

    # osu! API datastructure
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    ar: Mapped[float] = mapped_column(Float, nullable=False)
    beatmapset_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bpm: Mapped[float] = mapped_column(Float, nullable=False)
    checksum: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    count_circles: Mapped[int] = mapped_column(Integer, nullable=False)
    count_sliders: Mapped[int] = mapped_column(Integer, nullable=False)
    count_spinners: Mapped[int] = mapped_column(Integer, nullable=False)
    cs: Mapped[float] = mapped_column(Float, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(AwareDateTime())
    difficulty_rating: Mapped[float] = mapped_column(Float, nullable=False)
    drain: Mapped[float] = mapped_column(Float, nullable=False)
    failtimes: Mapped[dict[str, Optional[list[int]]]] = mapped_column(JSONB, nullable=False)
    hit_length: Mapped[int] = mapped_column(Integer, nullable=False)
    is_scoreable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    max_combo: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    mode_int: Mapped[int] = mapped_column(Integer, nullable=False)
    passcount: Mapped[int] = mapped_column(Integer, nullable=False)
    playcount: Mapped[int] = mapped_column(Integer, nullable=False)
    ranked: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    total_length: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    beatmapset_snapshots: Mapped[list["BeatmapsetSnapshot"]] = relationship(
        "BeatmapsetSnapshot",
        secondary=beatmap_snapshot_beatmapset_snapshot_association,
        back_populates="beatmap_snapshots",
        lazy=True
    )
    beatmap_tags: Mapped[list["BeatmapTag"]] = relationship(
        "BeatmapTag",
        secondary=beatmap_tag_beatmap_snapshot_association,
        lazy=True
    )
    leaderboard: Mapped["Leaderboard"] = relationship(
        "Leaderboard",
        uselist=False,
        back_populates="beatmap_snapshot",
        lazy=True
    )
    owner_profiles: Mapped[list["Profile"]] = relationship(
        "Profile",
        secondary=beatmap_snapshot_owner_association,
        lazy=True
    )

    __table_args__ = (
        UniqueConstraint("beatmap_id", "snapshot_number", name="_beatmap_and_snapshot_number_uc"),
    )
