import os
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import YamlConfigSettingsSource

from .enums import Env


_SECURITY_ENABLED_OVERRIDE: ContextVar[bool | None] = ContextVar(
    "security_enabled_override",
    default=None
)

_bootstrap_yaml_file: str = "config/bootstrap.yaml"


class QueueConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    name: str = "Graveboards Queue"
    description: str = "Master queue for beatmaps to receive leaderboards"
    user_id: int = 0


class UserConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    user_id: int
    roles: list[str] = ["admin"]
    generate_api_key: bool = True
    enable_score_fetcher: bool = True


class BootstrapConfig(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file="config/bootstrap.yaml",
        yaml_file_encoding="utf-8",
        extra="ignore"
    )

    master_queue: QueueConfig = QueueConfig()
    extra_queues: list[QueueConfig] = []
    initial_users: list[UserConfig] = []
    initial_roles: list[str] = ["admin"]
    setup_steps: list[str] = [
        "create_database",
        "seed_roles",
        "seed_users",
        "seed_api_keys",
        "seed_queues",
    ]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=_bootstrap_yaml_file),
            file_secret_settings,
        )


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self) -> None:
        load_dotenv()
        self.ENV = Env(os.getenv("ENV", "prod").lower())
        self.DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        self.DISABLE_SECURITY = os.getenv("DISABLE_SECURITY", "false").lower() in ("true", "1", "yes")
        self.DEBUG_API_KEY = os.getenv("DEBUG_API_KEY")

        self.PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.SPEC_DIR = os.path.abspath("api/v1/spec")
        self.OPENAPI_ENTRYPOINT = os.path.join(self.SPEC_DIR, "openapi.yaml")
        self.INSTANCE_DIR = os.path.abspath("instance")
        self.CACHE_FILE = os.path.join(self.INSTANCE_DIR, ".spec_cache.pkl")
        self.LOGS_DIR = os.path.join(self.INSTANCE_DIR, "logs")
        self.API_BASE_PATH = "api/v1/"
        self.DEFAULT_MODULE_NAME = "api.v1"

        self.FRONTEND_BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY must be provided in .env")

        self.POSTGRESQL_CONFIGURATION = {
            "drivername": "postgresql+asyncpg",
            "host": os.getenv("POSTGRESQL_HOST"),
            "port": os.getenv("POSTGRESQL_PORT"),
            "username": os.getenv("POSTGRESQL_USERNAME"),
            "password": os.getenv("POSTGRESQL_PASSWORD"),
            "database": os.getenv("POSTGRESQL_DATABASE")
        }

        self.REDIS_CONFIGURATION = {
            "host": os.getenv("REDIS_HOST"),
            "port": os.getenv("REDIS_PORT"),
            "username": os.getenv("REDIS_USERNAME"),
            "password": os.getenv("REDIS_PASSWORD"),
            "db": os.getenv("REDIS_DB"),
            "decode_responses": True,
            "protocol": 3
        }

        self.OAUTH_CONFIGURATION = {
            "client_id": os.getenv("OSU_CLIENT_ID"),
            "client_secret": os.getenv("OSU_CLIENT_SECRET"),
            "redirect_uri": self.FRONTEND_BASE_URL + "/callback",
            "authorize_url": "https://osu.ppy.sh/oauth/authorize",
            "token_endpoint": "https://osu.ppy.sh/oauth/token",
            "token_endpoint_auth_method": "client_secret_basic"
        }

        self.TEST_POSTGRESQL_CONFIGURATION = {
            "drivername": "postgresql+asyncpg",
            "host": os.getenv("TEST_POSTGRESQL_HOST", os.getenv("POSTGRESQL_HOST")),
            "port": os.getenv("TEST_POSTGRESQL_PORT", os.getenv("POSTGRESQL_PORT")),
            "username": os.getenv("TEST_POSTGRESQL_USERNAME", os.getenv("POSTGRESQL_USERNAME")),
            "password": os.getenv("TEST_POSTGRESQL_PASSWORD", os.getenv("POSTGRESQL_PASSWORD")),
            "database": os.getenv("TEST_POSTGRESQL_DATABASE", os.getenv("POSTGRESQL_DATABASE") + "_test")
        }

        self.TEST_REDIS_CONFIGURATION = {
            "host": os.getenv("TEST_REDIS_HOST", os.getenv("REDIS_HOST")),
            "port": os.getenv("TEST_REDIS_PORT", os.getenv("REDIS_PORT")),
            "username": os.getenv("TEST_REDIS_USERNAME", os.getenv("REDIS_USERNAME")),
            "password": os.getenv("TEST_REDIS_PASSWORD", os.getenv("REDIS_PASSWORD")),
            "db": int(os.getenv("TEST_REDIS_DB", os.getenv("REDIS_DB", "1"))),
            "decode_responses": True,
            "protocol": 3
        }

    @property
    def bootstrap(self) -> BootstrapConfig:
        global _bootstrap_yaml_file
        _bootstrap_yaml_file = "config/bootstrap.test.yaml" if self.ENV == Env.TEST else "config/bootstrap.yaml"
        return BootstrapConfig(_env_file=None)


CONFIG = Config()


def get_security_enabled() -> bool:
    """Return whether runtime security checks should be enforced."""
    override = _SECURITY_ENABLED_OVERRIDE.get()
    if override is not None:
        return override

    return os.getenv("DISABLE_SECURITY", "false").lower() not in ("true", "1", "yes")


@contextmanager
def override_security_enabled(enabled: bool) -> Iterator[None]:
    """Temporarily override runtime security enforcement."""
    token = _SECURITY_ENABLED_OVERRIDE.set(enabled)
    try:
        yield
    finally:
        _SECURITY_ENABLED_OVERRIDE.reset(token)


ENV = CONFIG.ENV
DEBUG = CONFIG.DEBUG
DISABLE_SECURITY = CONFIG.DISABLE_SECURITY
DEBUG_API_KEY = CONFIG.DEBUG_API_KEY
PROJECT_ROOT = CONFIG.PROJECT_ROOT
SPEC_DIR = CONFIG.SPEC_DIR
OPENAPI_ENTRYPOINT = CONFIG.OPENAPI_ENTRYPOINT
INSTANCE_DIR = CONFIG.INSTANCE_DIR
CACHE_FILE = CONFIG.CACHE_FILE
LOGS_DIR = CONFIG.LOGS_DIR
API_BASE_PATH = CONFIG.API_BASE_PATH
DEFAULT_MODULE_NAME = CONFIG.DEFAULT_MODULE_NAME
FRONTEND_BASE_URL = CONFIG.FRONTEND_BASE_URL
JWT_SECRET_KEY = CONFIG.JWT_SECRET_KEY
JWT_ALGORITHM = CONFIG.JWT_ALGORITHM
POSTGRESQL_CONFIGURATION = CONFIG.POSTGRESQL_CONFIGURATION
REDIS_CONFIGURATION = CONFIG.REDIS_CONFIGURATION
OAUTH_CONFIGURATION = CONFIG.OAUTH_CONFIGURATION
TEST_POSTGRESQL_CONFIGURATION = CONFIG.TEST_POSTGRESQL_CONFIGURATION
TEST_REDIS_CONFIGURATION = CONFIG.TEST_REDIS_CONFIGURATION
