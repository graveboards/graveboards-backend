import logging
import logging.config
import os
from pathlib import Path
from typing import Iterable

import yaml

from app.config import DEBUG

CONFIG_PATH = Path("logging.yaml")


def setup_logging(
    global_level: int = None,
    enabled_loggers: Iterable[str] = None,
    disabled_loggers: Iterable[str] = None,
    level_overrides: dict[str, int] = None,
    no_debug: bool = False,
    json_format: bool = None
):
    """Initialize application logging from YAML configuration.

    Args:
        global_level:
            Optional log level applied to all configured loggers.
        enabled_loggers:
            If provided, only these loggers retain handlers.
        disabled_loggers:
            Explicitly disable specific loggers.
        level_overrides:
            Per-logger level mapping.
        no_debug:
            If True, changes DEBUG-level loggers to INFO.
        json_format:
            If True, use JSON formatter for all handlers. If None, auto-detect
            from LOG_FORMAT env var (default: "text").

    Side Effects:
        - Creates log directory if missing.
        - Configures the global logging system.
    """
    if json_format is None:
        json_format = os.getenv("LOG_FORMAT", "text").lower() == "json"

    with open(CONFIG_PATH, "rt") as f:
        config = yaml.safe_load(f)

    loggers_config = config.get("loggers", {})

    if global_level is not None:
        if "root" in config:
            config["root"]["level"] = logging.getLevelName(global_level)

        for name in loggers_config:
            loggers_config[name]["level"] = logging.getLevelName(global_level)

    if enabled_loggers is not None:
        enabled_loggers = set(enabled_loggers)

        for name in loggers_config:
            if name not in enabled_loggers:
                loggers_config[name]["handlers"] = []
                loggers_config[name]["propagate"] = False

        if "root" in config:
            config["root"]["handlers"] = []

    if disabled_loggers is not None:
        for name in disabled_loggers:
            if name in loggers_config:
                loggers_config[name]["handlers"] = []
                loggers_config[name]["propagate"] = False

    if level_overrides is not None:
        for name, level in level_overrides.items():
            if name in loggers_config:
                loggers_config[name]["level"] = logging.getLevelName(level)

    if no_debug:
        for name in config["loggers"]:
            if name != "root":
                if config["loggers"][name]["level"] == logging.DEBUG:
                    config["loggers"][name]["level"] = logging.INFO
    elif DEBUG:
        for name in config["loggers"]:
            if name != "root":
                config["loggers"][name]["level"] = logging.DEBUG

    if json_format:
        _apply_json_format(config)

    logging.config.dictConfig(config)
    logging.getLogger("push_response").disabled = True


def _apply_json_format(config: dict) -> None:
    """Replace text formatters with JSON formatters in all handlers.

    Args:
        config:
            Logging configuration dictionary.
    """
    from .json_formatter import JSONLogFormatter

    json_formatter = JSONLogFormatter()

    for handler_config in config.get("handlers", {}).values():
        if "formatter" in handler_config:
            handler_config["formatter"] = "json"

    config["formatters"] = {
        "json": {
            "()": JSONLogFormatter,
        }
    }
