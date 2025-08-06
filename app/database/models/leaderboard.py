from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from .base import Base

if TYPE_CHECKING:
    from .score import Score


class Leaderboard(Base):
    __tablename__ = "leaderboards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmaps.id"), nullable=False)
    beatmap_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmap_snapshots.id"), nullable=False)

    # Relationships
    scores: Mapped[list["Score"]] = relationship("Score", lazy=True)

    __table_args__ = (
        UniqueConstraint("beatmap_id", "beatmap_snapshot_id", name="_beatmap_and_snapshot_uc"),
    )
