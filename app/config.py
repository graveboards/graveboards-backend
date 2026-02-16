import os
from pathlib import Path

from dotenv import load_dotenv

from .utils import parse_user_ids
from .enums import Env

load_dotenv()

ENV = Env(os.getenv("ENV", "prod").lower())
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
DISABLE_SECURITY = os.getenv("DISABLE_SECURITY", "false").lower() in ("true", "1", "yes")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_BASE_PATH = "api/v1/"
SPEC_DIR = os.path.abspath("api/v1/spec")
CACHE_FILE = os.path.join(SPEC_DIR, ".spec_cache.pkl")
OPENAPI_ENTRYPOINT = os.path.join(SPEC_DIR, "openapi.yaml")
DEFAULT_MODULE_NAME = "api.v1"
INSTANCE_DIR = os.path.abspath("instance")

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
