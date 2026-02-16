import logging
import copy

from .utils import get_alias
from .colors import *


class LogFormatter(logging.Formatter):
    def __init__(self, *args, colored: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.colored = colored

    def format(self, record: logging.LogRecord) -> str:
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
    