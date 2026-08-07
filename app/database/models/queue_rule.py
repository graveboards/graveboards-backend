"""Queue rule model configuring a queue's acceptance criteria."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import JSON, Boolean, DateTime, Integer, String

from app.utils import aware_utcnow

from .base import Base

if TYPE_CHECKING:
    from .queue import Queue


class QueueRule(Base):
    """An individual rule governing requests submitted to a queue."""

    __tablename__ = "queue_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )

    queue: Mapped[Queue] = relationship("Queue", back_populates="rules", lazy=True)
