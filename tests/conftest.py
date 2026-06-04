import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    os.environ.setdefault("ENV", "dev")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("DISABLE_SECURITY", "false")
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("ADMIN_USER_IDS", "1")
    os.environ.setdefault("BASE_URL", "http://localhost:3000")

    os.environ.setdefault("POSTGRESQL_HOST", "localhost")
    os.environ.setdefault("POSTGRESQL_PORT", "5432")
    os.environ.setdefault("POSTGRESQL_USERNAME", "postgres")
    os.environ.setdefault("POSTGRESQL_PASSWORD", "postgres")
    os.environ.setdefault("POSTGRESQL_DATABASE", "graveboards_test")

    os.environ.setdefault("REDIS_HOST", "localhost")
    os.environ.setdefault("REDIS_PORT", "6379")
    os.environ.setdefault("REDIS_DB", "15")
