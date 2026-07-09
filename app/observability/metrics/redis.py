from prometheus_client import Gauge, Counter, Histogram


redis_commands_total = Counter(
    "redis_commands_total",
    "Total number of Redis commands executed.",
    ["command", "status"],
)

redis_commands_duration_seconds = Histogram(
    "redis_commands_duration_seconds",
    "Redis command duration in seconds.",
    ["command"],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

redis_cache_hits_total = Counter(
    "redis_cache_hits_total",
    "Total number of Redis cache hits (GET commands returning data).",
)

redis_cache_misses_total = Counter(
    "redis_cache_misses_total",
    "Total number of Redis cache misses (GET commands returning None).",
)
