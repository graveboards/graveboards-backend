import logging
from inspect import FrameInfo
from pathlib import Path

from app.config import PROJECT_ROOT
from .adapter import Logger


def get_logger(name: str, **kwargs) -> Logger:
    """Return a contextual Logger adapter.

    Wraps a base logger (using its alias for handler routing) and attaches structured
    context via ``extra``.

    Args:
        name:
            Fully qualified logger name.
        **kwargs:
            Context fields injected into every log entry.

    Returns:
        Logger adapter instance.
    """
    base_logger = logging.getLogger(get_alias(name))
    base_logger.name = name

    return Logger(
        base_logger,
        extra=kwargs
    )


def get_alias(name: str) -> str:
    """Derive a short alias from a fully qualified logger name.

    For nested module paths, extracts a stable segment to use as the routing logger
    name. Special-cases external namespaces such as ``uvicorn`` and ``redis``.

    Args:
        name:
            Full logger name.

    Returns:
        Short alias string used for handler configuration.
    """
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
    """Emit a warning with caller location metadata.

    Formats a warning message including the calling function, relative file path, and
    line number. Useful for defensive logging and deprecation warnings.

    Args:
        logger:
            Logger adapter used to emit the warning.
        stack:
            Inspect stack frame list.
        message:
            Warning message body.
        frame:
            Stack frame index to inspect (default: caller).
    """
    caller_frame = stack[frame]
    lineno = caller_frame.lineno
    function = caller_frame.function
    filename = Path(caller_frame.filename).resolve()

    try:
        relative_path = filename.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_path = filename

    logger.warning(f"{message} | Called from: {function} ({relative_path}:{lineno})")
