from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.sql.schema import Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped

from app.utils import aware_utcnow
from .base import Base

if TYPE_CHECKING:
    pass


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    entity_id: Mapped[Optional[str]] = mapped_column(String(100))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_audit_timestamp", timestamp.desc()),
        Index("idx_audit_action", action),
        Index("idx_audit_entity", entity_type, entity_id),
    )
