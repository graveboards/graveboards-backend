from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base

if TYPE_CHECKING:
    from .queue import Queue


class QueueRestriction(Base):
    __tablename__ = "queue_restrictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False
    )
    restriction_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )

    queue: Mapped["Queue"] = relationship(
        "Queue",
        back_populates="restrictions",
        lazy=True
    )
