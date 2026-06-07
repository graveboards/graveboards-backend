from typing import TYPE_CHECKING

from sqlalchemy.sql import select
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.functions import func
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from .base import Base

if TYPE_CHECKING:
    from .beatmap import Beatmap
    from .beatmapset_snapshot import BeatmapsetSnapshot
    from .beatmapset_listing import BeatmapsetListing


class Beatmapset(Base):
    __tablename__ = "beatmapsets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    beatmaps: Mapped[list["Beatmap"]] = relationship(
        "Beatmap",
        back_populates="beatmapset",
        lazy=True
    )
    snapshots: Mapped[list["BeatmapsetSnapshot"]] = relationship(
        "BeatmapsetSnapshot",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )
    listings: Mapped[list["BeatmapsetListing"]] = relationship(
        "BeatmapsetListing",
        back_populates="beatmapset",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )

    # Hybrid annotations
    num_snapshots: Mapped[int]

    @hybrid_property
    def num_snapshots(self) -> int:
        return len(self.snapshots)

    @num_snapshots.expression
    def num_snapshots(cls):
        return (
            select(func.count(BeatmapsetSnapshot.id))
            .where(BeatmapsetSnapshot.beatmapset_id == cls.id)
            .scalar_subquery()
        )
