import logging
import os
import sys
from inspect import FrameInfo
from pathlib import Path

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    add_exc_info,
    add_log_level,
    StackInfoRenderer,
    TimeStamper,
)
from structlog.stdlib import ProcessorFormatter

from app.config import DEBUG, PROJECT_ROOT


SERVICE_NAME = "backend"


def _is_json_format() -> bool:
    return os.getenv("LOG_FORMAT", "text").lower() == "json"


def _get_level_overrides() -> dict[str, int]:
    overrides: dict[str, int] = {}

    if not DEBUG:
        overrides["app"] = logging.INFO

    overrides["uvicorn.access"] = logging.CRITICAL
    overrides["watchfiles"] = logging.WARNING

    return overrides


def setup_logging(
    enabled_loggers=None,
    disabled_loggers=None,
    level_overrides=None,
    no_debug=False,
    global_level=None,
) -> None:
    level = logging.DEBUG if DEBUG else logging.INFO
    json_format = _is_json_format()
    level_overrides = {**_get_level_overrides(), **(level_overrides or {})}

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            add_log_level,
            add_exc_info,
            StackInfoRenderer(),
            TimeStamper(fmt="iso", utc=False),
            structlog.processors.UnicodeDecoder(),
            _build_final_renderer(json_format),
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

    _configure_stdlib_bridge(json_format)


def _build_final_renderer(json_format: bool):
    if json_format:
        return structlog.processors.JSONRenderer(
            sort_keys=True,
            ensure_ascii=False,
        )

    return ConsoleRenderer(
        colors=True,
        exception_formatter=structlog.dev.TracebackRenderer(),
    )


def _configure_stdlib_bridge(json_format: bool) -> None:
    formatter = ProcessorFormatter(
        processor=_build_final_renderer(json_format),
        foreign_pre_chain=[
            structlog.stdlib.ExtraAdder(),
        ],
        allow_exc_info=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False


def get_logger(name: str, **kwargs) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name, service=SERVICE_NAME, **kwargs)


def clear_request_context() -> None:
    clear_contextvars()
    bind_contextvars(request_id=None)


def log_stack_warning(
    logger: structlog.stdlib.BoundLogger,
    stack: list[FrameInfo],
    message: str,
    frame: int = 1,
) -> None:
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
