from __future__ import annotations
from datetime import datetime

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.sqltypes import DateTime, Integer, String

from app.utils import aware_utcnow

from .base import Base


class BeatmapTag(Base):
    __tablename__ = "beatmap_tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    ruleset_id: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )
