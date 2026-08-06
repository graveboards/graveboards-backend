"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
    format_exc_info,
)
from structlog.stdlib import ProcessorFormatter

from app.config import DEBUG, LOGS_DIR, PROJECT_ROOT

if TYPE_CHECKING:
    from inspect import FrameInfo

SERVICE_NAME = "backend"
Logger = structlog.stdlib.BoundLogger

# Structured JSON sink for the monitoring stack (promtail tails this file).
# Kept separate from stdout so stdout can stay human-readable in every
# environment — no LOG_FORMAT env var needed, both sinks are always on.
JSON_LOG_FILE = Path(LOGS_DIR) / "app.jsonl"


def _get_level_overrides() -> dict[str, int]:
    overrides: dict[str, int] = {}

    if not DEBUG:
        overrides["app"] = logging.INFO

    overrides["uvicorn.access"] = logging.CRITICAL
    overrides["watchfiles"] = logging.WARNING

    return overrides


def _drop_color_message(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Discard uvicorn's ``color_message`` extra so it never leaks into output."""
    event_dict.pop("color_message", None)
    return event_dict


def _build_shared_processors() -> list:
    """Processors applied to *both* native structlog and foreign stdlib records.

    Foreign records (uvicorn, sqlalchemy) run these via the ProcessorFormatter's
    ``foreign_pre_chain``; native records run them in ``structlog.configure``.
    Keeping a single list is what makes every log line render identically.
    """
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        add_log_level,
        _drop_color_message,
        StackInfoRenderer(),
        format_exc_info,
        # utc=True so the ISO timestamp ends in "Z" (or a numeric offset for
        # non-UTC fmts) — promtail's timestamp stage requires an explicit
        # offset marker and otherwise falls back to ingest time.
        TimeStamper(fmt="iso", utc=True),
        structlog.processors.UnicodeDecoder(),
    ]


def setup_logging(
    enabled_loggers: list[str] | None = None,  # noqa: ARG001
    disabled_loggers: list[str] | None = None,  # noqa: ARG001
    level_overrides: dict[str, int] | None = None,
    no_debug: bool = False,
    global_level: int | None = None,  # noqa: ARG001
) -> None:
    """Configure structlog and stdlib logging for the application.

    Sets up dual sinks (console + JSON file) with shared processors so both
    human-readable and machine-parsable logs are emitted identically.

    Args:
        enabled_loggers:
            Reserved for future use.
        disabled_loggers:
            Reserved for future use.
        level_overrides:
            Additional logger name to level mappings.
        no_debug:
            Force INFO level regardless of DEBUG setting.
        global_level:
            Reserved for future use.
    """
    level = logging.INFO if no_debug else logging.DEBUG if DEBUG else logging.INFO
    level_overrides = {**_get_level_overrides(), **(level_overrides or {})}
    shared_processors = _build_shared_processors()

    structlog.configure(
        processors=[
            *shared_processors,
            # Hand the event dict off to the stdlib ProcessorFormatter instead of
            # rendering here, so native and foreign records share one renderer.
            ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    for name, log_level in level_overrides.items():
        logging.getLogger(name).setLevel(log_level)

    logging.getLogger("app").setLevel(level)
    logging.getLogger("root").setLevel(logging.WARNING)

    _configure_stdlib_bridge(shared_processors)


def _build_handlers(shared_processors: list) -> list[logging.Handler]:
    """Two independent sinks fed by the same log records.

    Console: human-readable, always on, whatever runs `docker compose logs`
    or a bare terminal sees the same clean output in dev and prod.

    JSON file: structured, always on, what promtail tails and ships to Loki.
    Splitting these out means neither audience has to compromise, and no
    LOG_FORMAT env var is needed to pick one over the other.
    """
    console_formatter = ProcessorFormatter(
        processors=[
            ProcessorFormatter.remove_processors_meta,
            ConsoleRenderer(colors=True),
        ],
        foreign_pre_chain=shared_processors,
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    JSON_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    json_formatter = ProcessorFormatter(
        processors=[
            ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(sort_keys=True, ensure_ascii=False),
        ],
        foreign_pre_chain=shared_processors,
    )
    json_handler = logging.handlers.RotatingFileHandler(
        JSON_LOG_FILE,
        maxBytes=50 * 1024 * 1024,
        backupCount=5,
    )
    json_handler.setFormatter(json_formatter)

    return [console_handler, json_handler]


def _configure_stdlib_bridge(shared_processors: list) -> None:
    handlers = _build_handlers(shared_processors)

    root = logging.getLogger()
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = False


def get_logger(name: str, **kwargs: Any) -> structlog.stdlib.BoundLogger:
    """Get a named structlog bound logger.

    Args:
        name:
            Logger name.
        **kwargs:
            Additional key-value pairs bound to every log record.

    Returns:
        A structlog bound logger instance.
    """
    return structlog.get_logger(name, service=SERVICE_NAME, **kwargs)  # type: ignore[no-any-return]


def clear_request_context() -> None:
    """Clear request-scoped context variables."""


def log_stack_warning(
    logger: structlog.stdlib.BoundLogger,
    stack: list[FrameInfo],
    message: str,
    frame: int = 1,
) -> None:
    """Log a warning with caller frame information.

    Args:
        logger:
            The logger to use.
        stack:
            The call stack to inspect.
        message:
            The warning message.
        frame:
            Stack frame index to report.
    """
    caller_frame = stack[frame]
    lineno = caller_frame.lineno
    function = caller_frame.function
    filename = Path(caller_frame.filename).resolve()

    try:
        relative_path = filename.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_path = filename

    logger.warning(
        "%s | Called from: %s (%s:%s)",
        message,
        function,
        relative_path,
        lineno,
    )
