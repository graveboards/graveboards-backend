import os

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
DISABLE_SECURITY = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

SPEC_DIR = os.path.abspath("api/v1")
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

_admin_user_ids = os.getenv("ADMIN_USER_IDS", []).split(",")
ADMIN_USER_IDS = {int(user_id.strip()) for user_id in _admin_user_ids or {}}

if not ADMIN_USER_IDS:
    raise ValueError("ADMIN_USER_IDS must be provided in .env (at least one ID)")

PRIVILEGED_USER_IDS = {int(user_id.strip()) for user_id in os.getenv("PRIVILEGED_USER_IDS", set()).split(",")}
PRIMARY_ADMIN_USER_ID = int(_admin_user_ids[0].strip())
MASTER_QUEUE_NAME = "Graveboards Queue"
MASTER_QUEUE_DESCRIPTION = "Master queue for beatmaps to receive leaderboards"
