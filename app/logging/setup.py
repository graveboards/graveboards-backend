import os
import logging
import logging.config
from pathlib import Path
from typing import Iterable

import yaml

from app.config import DEBUG

CONFIG_PATH = Path("logging.yaml")
LOGS_DIR = Path("instance/logs")


def setup_logging(
    global_level: int = None,
    enabled_loggers: Iterable[str] = None,
    disabled_loggers: Iterable[str] = None,
    level_overrides: dict[str, int] = None,
    no_debug: bool = False
):
    with open(CONFIG_PATH, "rt") as f:
        config = yaml.safe_load(f)

    os.makedirs(LOGS_DIR, exist_ok=True)

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

    logging.config.dictConfig(config)
    logging.getLogger("push_response").disabled = True
