"""Audit log model recording user actions on the platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import JSON, DateTime, Integer, String, Text

from app.utils import aware_utcnow

from .base import Base


class AuditLog(Base):
    """An audit log entry capturing an audited action."""

    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    user_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("idx_audit_timestamp", timestamp.desc()),
        Index("idx_audit_action", action),
        Index("idx_audit_entity", entity_type, entity_id),
    )
