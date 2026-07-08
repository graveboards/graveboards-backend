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
):
    """Initialize application logging.

    Dev  (LOG_FORMAT not set or 'text'):  colored text to terminal + file rotation
    Prod (LOG_FORMAT='json'):             JSON to stdout for Loki/Promtail

    Configures all loggers including uvicorn.* so startup/error messages
    use the same formatter as app logs.

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

    Side Effects:
        - Creates log directory if missing.
        - Configures the global logging system.
    """
    is_json = os.getenv("LOG_FORMAT", "text").lower() == "json"

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

    if is_json:
        _configure_json_mode(config)
    else:
        _configure_text_mode(config)

    logging.config.dictConfig(config)
    logging.getLogger("push_response").disabled = True


def _configure_json_mode(config: dict) -> None:
    """Strip file handlers and switch console to JSON for container output."""
    config["handlers"]["console"]["formatter"] = "json"

    # Remove all file handlers
    for name in list(config["handlers"]):
        if name != "console":
            config["handlers"].pop(name)

    # Remove file handlers from all loggers — only console remains
    for logger_cfg in config["loggers"].values():
        logger_cfg["handlers"] = [
            h for h in logger_cfg["handlers"] if h == "console"
        ]


def _configure_text_mode(config: dict) -> None:
    """Ensure console uses colored formatter for terminal dev output.

    File handlers stay active for local debugging.
    Disables uvicorn's built-in access logging (our AccessLogMiddleware handles it).
    """
    config["handlers"]["console"]["formatter"] = "colored"
    
    # Disable uvicorn's built-in access logger to avoid duplicates with AccessLogMiddleware
    config["loggers"]["uvicorn.access"]["level"] = "CRITICAL"
