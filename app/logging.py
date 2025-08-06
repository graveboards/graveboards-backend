import os
import logging
import logging.config
from pathlib import Path

import yaml

from app.config import DEBUG

CONFIG_PATH = Path("logging.yaml")
LOGS_DIR = Path("instance/logs")


def setup_logging():
    with open(CONFIG_PATH, "rt") as f:
        config = yaml.safe_load(f)

    os.makedirs(LOGS_DIR, exist_ok=True)

    if DEBUG:
        for name in {"app", "daemon"}:
            config["loggers"][name]["level"] = logging.DEBUG

    logging.config.dictConfig(config)
    logging.getLogger("push_response").disabled = True
