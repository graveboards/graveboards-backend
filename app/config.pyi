from contextlib import AbstractContextManager
from enum import Enum
from pathlib import Path
from typing import Any

class Env(Enum):
    PROD = "prod"
    DEV = "dev"
    TEST = "test"

class QueueConfig:
    name: str
    description: str
    user_id: int

class UserConfig:
    user_id: int
    roles: list[str]
    generate_api_key: bool
    enable_score_fetcher: bool

class BootstrapConfig:
    master_queue: QueueConfig
    extra_queues: list[QueueConfig]
    initial_users: list[UserConfig]
    initial_roles: list[str]
    setup_steps: list[str]

class Config:
    ENV: Env
    DEBUG: bool
    DISABLE_SECURITY: bool
    DEBUG_API_KEY: str | None
    DEV_ADMIN_USER_ID: int
    DEV_USER_ID: int
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
    TEST_POSTGRESQL_CONFIGURATION: dict[str, Any]
    TEST_REDIS_CONFIGURATION: dict[str, Any]
    bootstrap: property

CONFIG: Config
ENV: Env
DEBUG: bool
DISABLE_SECURITY: bool
DEBUG_API_KEY: str | None
DEV_ADMIN_USER_ID: int
DEV_USER_ID: int
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
TEST_POSTGRESQL_CONFIGURATION: dict[str, Any]
TEST_REDIS_CONFIGURATION: dict[str, Any]

def get_security_enabled() -> bool: ...
def override_security_enabled(enabled: bool) -> AbstractContextManager[None]: ...
