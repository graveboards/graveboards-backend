import structlog

from app.observability.logging import (
    clear_request_context,
    get_logger,
    log_stack_warning,
    setup_logging,
)

Logger = structlog.stdlib.BoundLogger

__all__ = [
    "setup_logging",
    "Logger",
    "get_logger",
    "log_stack_warning",
    "clear_request_context",
]
