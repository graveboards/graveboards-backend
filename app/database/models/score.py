from datetime import datetime
from typing import Optional

from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.dialects.postgresql.json import JSONB

from .base import Base


class Score(Base):
    __tablename__ = "scores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    beatmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmaps.id"), nullable=False)
    beatmapset_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapsets.id"), nullable=False)
    leaderboard_id: Mapped[int] = mapped_column(Integer, ForeignKey("leaderboards.id"), nullable=False)

    # osu! API datastructure
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_combo: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    mode_int: Mapped[int] = mapped_column(Integer, nullable=False)
    mods: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    perfect: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pp: Mapped[Optional[float]] = mapped_column(Float)
    rank: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    statistics: Mapped[dict[str, Optional[int]]] = mapped_column(JSONB, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "beatmap_id", "created_at", name="_user_and_beatmap_and_creation_uc"),
    )
