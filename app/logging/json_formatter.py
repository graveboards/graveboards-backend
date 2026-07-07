import json
import logging
import time

from app.metrics.request_id import get_request_id
from .utils import get_alias


class JSONLogFormatter(logging.Formatter):
    """JSON log formatter for structured logging compatible with Loki/Promtail.

    Outputs logs as JSON objects with consistent fields for log aggregation.
    Each log entry includes: timestamp, level, logger, message, request_id,
    and any extra fields passed via logger.info(..., extra={...}).

    Designed for use with Loki/Promtail log aggregation.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Args:
            record:
                ``LogRecord`` to format.

        Returns:
            JSON-formatted log string.
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id() or "",
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields (passed via logger.info(..., extra={...}))
        for key, value in record.__dict__.items():
            if key not in ("asctime", "created", "elapsed", "exc_info", "exc_text",
                          "filename", "funcName", "levelname", "levelno", "lineno",
                          "message", "module", "msecs", "msg", "name", "pathname",
                          "process", "processName", "relativeCreated", "stack_info",
                          "thread", "threadName", "taskName", "alias", "request_id",
                          "prefix"):
                try:
                    log_data[key] = value
                except TypeError:
                    log_data[key] = str(value)

        return json.dumps(log_data, default=str, ensure_ascii=False)
