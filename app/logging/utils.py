import logging
from inspect import FrameInfo
from pathlib import Path

from app.config import PROJECT_ROOT
from .adapter import Logger


def get_logger(name: str, **kwargs) -> Logger:
    base_logger = logging.getLogger(get_alias(name))
    base_logger.name = name

    return Logger(
        base_logger,
        extra=kwargs
    )


def get_alias(name: str) -> str:
    if "." in name:
        path = name.split(".")

        if name.startswith(("uvicorn", "redis")):
            alias = path[0]
        else:
            alias = path[1]
    else:
        alias = name

    return alias


def log_stack_warning(logger: Logger, stack: list[FrameInfo], message: str, frame: int = 1):
    caller_frame = stack[frame]
    lineno = caller_frame.lineno
    function = caller_frame.function
    filename = Path(caller_frame.filename).resolve()

    try:
        relative_path = filename.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_path = filename

    logger.warning(f"{message} | Called from: {function} ({relative_path}:{lineno})")
