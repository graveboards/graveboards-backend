from prometheus_client import Counter, Histogram, Gauge
from .registry import REGISTRY


daemon_service_running = Gauge(
    "daemon_service_running",
    "Whether a daemon service is currently running (1) or not (0).",
    ["service"],
    registry=REGISTRY,
)

daemon_jobs_total = Counter(
    "daemon_jobs_total",
    "Total number of daemon jobs executed.",
    ["service", "status"],
    registry=REGISTRY,
)

daemon_job_duration_seconds = Histogram(
    "daemon_job_duration_seconds",
    "Duration of daemon job executions in seconds.",
    ["service"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=REGISTRY,
)

daemon_last_job_timestamp = Gauge(
    "daemon_last_job_timestamp",
    "Timestamp of the last successful daemon job execution (Unix epoch).",
    ["service"],
    registry=REGISTRY,
)

daemon_active_jobs = Gauge(
    "daemon_active_jobs",
    "Number of currently active daemon jobs.",
    ["service"],
    registry=REGISTRY,
)
