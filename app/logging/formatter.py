import logging
import copy

from .utils import get_alias
from .colors import *


class LogFormatter(logging.Formatter):
    """Custom formatter with aliasing and optional ANSI coloring.

    Behavior and features:
        - Rewrites logger names into short aliases
        - Supports structured prefix injection
        - Optionally applies ANSI color codes by level
        - Ensures safe record mutation via shallow copy

    Designed to unify logging formats while allowing colored console output.
    """
    def __init__(self, *args, colored: bool = False, **kwargs):
        """Initialize formatter.

        Args:
            colored:
                Whether to apply ANSI color formatting.
        """
        super().__init__(*args, **kwargs)
        self.colored = colored

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with aliasing and optional coloring.

        Applies:
            - Alias transformation
            - Prefix formatting
            - Level-based coloring (if enabled)

        Args:
            record:
                ``LogRecord`` to format.

        Returns:
            Fully formatted log string.
        """
        record = copy.copy(record)
        record.alias = get_alias(record.name)

        if asctime := getattr(record, "asctime", None):
            record.asctime = asctime
        else:
            record.asctime = ""

        if prefix := getattr(record, "prefix", None):
            record.prefix = f"[{prefix}] "
        else:
            record.prefix = ""

        if self.colored:
            level_color = LEVEL_COLORS.get(record.levelname, "")
            alias_color = ALIAS_COLORS.get(record.levelname, "")
            record.asctime = f"{ASCTIME}{record.asctime}{RESET}"
            record.levelname = f"{level_color}{record.levelname:<8}{RESET}"
            record.alias = f"{alias_color}{record.alias:<8}{RESET}"
            record.prefix = f"{PREFIX}{record.prefix}{RESET}"
            record.msg = f"{MSG}{record.msg}{RESET}"

        return super().format(record)
    