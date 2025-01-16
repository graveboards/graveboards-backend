import os

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

SPEC_DIR = os.path.abspath("api/v1")
INSTANCE_DIR = os.path.abspath("instance")

FRONTEND_BASE_URL = os.getenv("BASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

POSTGRESQL_CONFIGURATION = {
    "drivername": "postgresql+psycopg",
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
    "db": os.getenv("REDIS_DB")
}

OAUTH_CONFIGURATION = {
    "client_id": os.getenv("OSU_CLIENT_ID"),
    "client_secret": os.getenv("OSU_CLIENT_SECRET"),
    "redirect_uri": FRONTEND_BASE_URL + "/callback",
    "authorize_url": "https://osu.ppy.sh/oauth/authorize",
    "token_endpoint": "https://osu.ppy.sh/oauth/token",
    "token_endpoint_auth_method": "client_secret_basic"
}

ADMIN_USER_IDS = [int(user_id.strip()) for user_id in os.getenv("ADMIN_USER_IDS").split(",")]
PRIMARY_ADMIN_USER_ID = ADMIN_USER_IDS[0]
MASTER_QUEUE_NAME = "Graveboards Queue"
MASTER_QUEUE_DESCRIPTION = "Master queue for beatmaps to receive leaderboards"
