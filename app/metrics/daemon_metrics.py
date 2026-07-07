from prometheus_client import Counter, Histogram, Gauge
from .registry import REGISTRY


daemon_runs_total = Counter(
    "daemon_runs_total",
    "Total number of daemon service runs.",
    ["service", "status"],
    registry=REGISTRY,
)

daemon_run_duration_seconds = Histogram(
    "daemon_run_duration_seconds",
    "Duration of daemon service runs in seconds.",
    ["service"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY,
)

daemon_last_run_timestamp = Gauge(
    "daemon_last_run_timestamp",
    "Timestamp of the last successful daemon service run (Unix epoch).",
    ["service"],
    registry=REGISTRY,
)

daemon_total_failures = Counter(
    "daemon_total_failures",
    "Total number of daemon service task failures.",
    ["service"],
    registry=REGISTRY,
)

daemon_critical_failures = Counter(
    "daemon_critical_failures",
    "Total number of daemon service critical task failures.",
    ["service"],
    registry=REGISTRY,
)
