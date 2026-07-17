from __future__ import annotations

from typing import Optional

from app.logging import get_logger
from app.utils import aware_utcnow

logger = get_logger(__name__)

_audit_buffer: list[dict] = []
_BUFFER_SIZE = 50
_FLUSH_INTERVAL = 5

_db: PostgresqlDB | None = None


async def _get_shared_db() -> PostgresqlDB:
    """Lazily create and cache the shared DB instance for audit flushing."""
    global _db
    if _db is None:
        from app.database import PostgresqlDB
        _db = PostgresqlDB()
    return _db


async def audit_log(
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Record an audit event.

    Events are buffered and flushed in batches for performance.
    Also written to structlog for Loki ingestion.
    """
    event = {
        "timestamp": aware_utcnow(),
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    logger.info(
        f"AUDIT: {action}",
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
    )

    _audit_buffer.append(event)
    if len(_audit_buffer) >= _BUFFER_SIZE:
        await _flush_buffer()


async def _flush_buffer():
    """Flush buffered audit events to database."""
    global _audit_buffer
    if not _audit_buffer:
        return

    events = _audit_buffer
    _audit_buffer = []

    try:
        from app.database.models import AuditLog

        db = await _get_shared_db()
        async with db.session() as session:
            for event in events:
                record = AuditLog(**event)
                session.add(record)
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to flush audit buffer: {e}")
        _audit_buffer = events + _audit_buffer
