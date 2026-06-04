__all__ = [
    "setup_logging",
    "Logger",
    "LogFormatter",
    "get_logger",
    "log_stack_warning",
]


def __getattr__(name):
    if name == "setup_logging":
        from .setup import setup_logging

        return setup_logging

    if name == "Logger":
        from .adapter import Logger

        return Logger

    if name == "LogFormatter":
        from .formatter import LogFormatter

        return LogFormatter

    if name in {"get_logger", "log_stack_warning"}:
        from . import utils

        return getattr(utils, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
