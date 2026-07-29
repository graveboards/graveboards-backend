from __future__ import annotations
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql import select
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer

from .base import Base

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshot
    from .beatmapset import Beatmapset


class Beatmap(Base):
    __tablename__ = "beatmaps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    beatmapset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("beatmapsets.id"), nullable=False
    )

    # Relationships
    beatmapset: Mapped[list[Beatmapset]] = relationship(
        "Beatmapset", back_populates="beatmaps", lazy=True
    )
    snapshots: Mapped[list[BeatmapSnapshot]] = relationship("BeatmapSnapshot", lazy=True)

    # Hybrid annotations
    @hybrid_property
    def num_snapshots(self) -> int:
        return len(self.snapshots)

    @num_snapshots.expression
    @classmethod
    def _num_snapshots_expr(cls) -> Any:
        return (
            select(func.count(BeatmapSnapshot.id))
            .where(BeatmapSnapshot.beatmap_id == cls.id)
            .scalar_subquery()
        )
