from enum import Enum
from pathlib import Path
from typing import Any

class Env(Enum):
    PROD = "prod"
    DEV = "dev"
    TEST = "test"


ENV: Env
DEBUG: bool
DISABLE_SECURITY: bool
DEBUG_API_KEY: str | None
PROJECT_ROOT: Path
SPEC_DIR: str
OPENAPI_ENTRYPOINT: str
INSTANCE_DIR: str
CACHE_FILE: str
LOGS_DIR: str
API_BASE_PATH: str
DEFAULT_MODULE_NAME: str
FRONTEND_BASE_URL: str
JWT_SECRET_KEY: str
JWT_ALGORITHM: str
POSTGRESQL_CONFIGURATION: dict[str, Any]
REDIS_CONFIGURATION: dict[str, Any]
OAUTH_CONFIGURATION: dict[str, Any]
ADMIN_USER_IDS: set[int]
PRIMARY_ADMIN_USER_ID: int
MASTER_QUEUE_NAME: str
MASTER_QUEUE_DESCRIPTION: str
TEST_POSTGRESQL_CONFIGURATION: dict[str, Any]
TEST_REDIS_CONFIGURATION: dict[str, Any]

def load_config() -> dict[str, Any]: ...
