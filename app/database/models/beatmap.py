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
    from .beatmapset import Beatmapset
    from .beatmap_snapshot import BeatmapSnapshot


class Beatmap(Base):
    __tablename__ = "beatmaps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmapset_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapsets.id"), nullable=False)

    # Relationships
    beatmapset: Mapped[list["Beatmapset"]] = relationship(
        "Beatmapset",
        back_populates="beatmaps",
        lazy=True
    )
    snapshots: Mapped[list["BeatmapSnapshot"]] = relationship(
        "BeatmapSnapshot",
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
            select(func.count(BeatmapSnapshot.id))
            .where(BeatmapSnapshot.beatmap_id == cls.id)
            .scalar_subquery()
        )
