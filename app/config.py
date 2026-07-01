import os
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv

from .utils import parse_user_ids
from .enums import Env


_SECURITY_ENABLED_OVERRIDE: ContextVar[bool | None] = ContextVar(
    "security_enabled_override",
    default=None
)


def load_config() -> dict:
    """Load configuration from environment variables. No caching - reloads on each call."""
    load_dotenv()
    ENV_VALUE = Env(os.getenv("ENV", "prod").lower())
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    DISABLE_SECURITY = os.getenv("DISABLE_SECURITY", "false").lower() in ("true", "1", "yes")
    DEBUG_API_KEY = os.getenv("DEBUG_API_KEY")
    
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    SPEC_DIR = os.path.abspath("api/v1/spec")
    OPENAPI_ENTRYPOINT = os.path.join(SPEC_DIR, "openapi.yaml")
    INSTANCE_DIR = os.path.abspath("instance")
    CACHE_FILE = os.path.join(INSTANCE_DIR, ".spec_cache.pkl")
    LOGS_DIR = os.path.join(INSTANCE_DIR, "logs")
    API_BASE_PATH = "api/v1/"
    DEFAULT_MODULE_NAME = "api.v1"
    
    FRONTEND_BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be provided in .env")
    
    POSTGRESQL_CONFIGURATION = {
        "drivername": "postgresql+asyncpg",
        "host": os.getenv("POSTGRESQL_HOST"),
        "port": os.getenv("POSTGRESQL_PORT"),
        "username": os.getenv("POSTGRESQL_USERNAME"),
        "password": os.getenv("POSTGRESQL_PASSWORD"),
        "database": os.getenv("POSTGRESQL_DATABASE")
    }
    
    REDIS_CONFIGURATION = {
        "host": os.getenv("REDIS_HOST"),
        "port": os.getenv("REDIS_PORT"),
        "username": os.getenv("REDIS_USERNAME"),
        "password": os.getenv("REDIS_PASSWORD"),
        "db": os.getenv("REDIS_DB"),
        "decode_responses": True,
        "protocol": 3
    }
    
    OAUTH_CONFIGURATION = {
        "client_id": os.getenv("OSU_CLIENT_ID"),
        "client_secret": os.getenv("OSU_CLIENT_SECRET"),
        "redirect_uri": FRONTEND_BASE_URL + "/callback",
        "authorize_url": "https://osu.ppy.sh/oauth/authorize",
        "token_endpoint": "https://osu.ppy.sh/oauth/token",
        "token_endpoint_auth_method": "client_secret_basic"
    }
    
    ADMIN_USER_IDS = set(_admin_user_ids := parse_user_ids("ADMIN_USER_IDS", required=True))
    PRIMARY_ADMIN_USER_ID = _admin_user_ids[0]
    MASTER_QUEUE_NAME = "Graveboards Queue"
    MASTER_QUEUE_DESCRIPTION = "Master queue for beatmaps to receive leaderboards"
    
    # Test configuration - use separate DB/Redis for clean isolation
    TEST_POSTGRESQL_CONFIGURATION = {
        "drivername": "postgresql+asyncpg",
        "host": os.getenv("TEST_POSTGRESQL_HOST", os.getenv("POSTGRESQL_HOST")),
        "port": os.getenv("TEST_POSTGRESQL_PORT", os.getenv("POSTGRESQL_PORT")),
        "username": os.getenv("TEST_POSTGRESQL_USERNAME", os.getenv("POSTGRESQL_USERNAME")),
        "password": os.getenv("TEST_POSTGRESQL_PASSWORD", os.getenv("POSTGRESQL_PASSWORD")),
        "database": os.getenv("TEST_POSTGRESQL_DATABASE", os.getenv("POSTGRESQL_DATABASE") + "_test")
    }
    
    TEST_REDIS_CONFIGURATION = {
        "host": os.getenv("TEST_REDIS_HOST", os.getenv("REDIS_HOST")),
        "port": os.getenv("TEST_REDIS_PORT", os.getenv("REDIS_PORT")),
        "username": os.getenv("TEST_REDIS_USERNAME", os.getenv("REDIS_USERNAME")),
        "password": os.getenv("TEST_REDIS_PASSWORD", os.getenv("REDIS_PASSWORD")),
        "db": int(os.getenv("TEST_REDIS_DB", os.getenv("REDIS_DB", "1"))),
        "decode_responses": True,
        "protocol": 3
    }
    
    return {
        "ENV": ENV_VALUE,
        "DEBUG": DEBUG,
        "DISABLE_SECURITY": DISABLE_SECURITY,
        "DEBUG_API_KEY": DEBUG_API_KEY,
        "PROJECT_ROOT": PROJECT_ROOT,
        "SPEC_DIR": SPEC_DIR,
        "OPENAPI_ENTRYPOINT": OPENAPI_ENTRYPOINT,
        "INSTANCE_DIR": INSTANCE_DIR,
        "CACHE_FILE": CACHE_FILE,
        "LOGS_DIR": LOGS_DIR,
        "API_BASE_PATH": API_BASE_PATH,
        "DEFAULT_MODULE_NAME": DEFAULT_MODULE_NAME,
        "FRONTEND_BASE_URL": FRONTEND_BASE_URL,
        "JWT_SECRET_KEY": JWT_SECRET_KEY,
        "JWT_ALGORITHM": JWT_ALGORITHM,
        "POSTGRESQL_CONFIGURATION": POSTGRESQL_CONFIGURATION,
        "REDIS_CONFIGURATION": REDIS_CONFIGURATION,
        "OAUTH_CONFIGURATION": OAUTH_CONFIGURATION,
        "ADMIN_USER_IDS": ADMIN_USER_IDS,
        "PRIMARY_ADMIN_USER_ID": PRIMARY_ADMIN_USER_ID,
        "MASTER_QUEUE_NAME": MASTER_QUEUE_NAME,
        "MASTER_QUEUE_DESCRIPTION": MASTER_QUEUE_DESCRIPTION,
        "TEST_POSTGRESQL_CONFIGURATION": TEST_POSTGRESQL_CONFIGURATION,
        "TEST_REDIS_CONFIGURATION": TEST_REDIS_CONFIGURATION,
    }


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


globals().update(load_config())
