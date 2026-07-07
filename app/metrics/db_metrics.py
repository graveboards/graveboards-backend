from prometheus_client import Gauge, Histogram
from .registry import REGISTRY


db_pool_size = Gauge(
    "db_pool_size",
    "Maximum number of connections in the database connection pool.",
    registry=REGISTRY,
)

db_pool_checked_out = Gauge(
    "db_pool_checked_out",
    "Number of connections currently checked out from the pool.",
    registry=REGISTRY,
)

db_pool_checked_in = Gauge(
    "db_pool_checked_in",
    "Number of connections currently checked into the pool.",
    registry=REGISTRY,
)

db_pool_overflow = Gauge(
    "db_pool_overflow",
    "Number of overflow connections currently in use.",
    registry=REGISTRY,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds.",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=REGISTRY,
)


def classify_query(sql: str) -> str:
    sql_stripped = sql.strip().upper()
    if sql_stripped.startswith("SELECT"):
        return "select"
    elif sql_stripped.startswith("INSERT"):
        return "insert"
    elif sql_stripped.startswith("UPDATE"):
        return "update"
    elif sql_stripped.startswith("DELETE"):
        return "delete"
    elif sql_stripped.startswith("WITH"):
        return "cte"
    else:
        return "other"
