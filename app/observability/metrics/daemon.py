import os
from prometheus_client import Counter, Histogram, Gauge


def _get_commit_hash() -> str:
    # Baked in at image-build time via the GIT_COMMIT build arg (see Dockerfile);
    # the running container has no .git directory and no git binary to introspect.
    return os.environ.get("GIT_COMMIT", "unknown")


graveboards_build_info = Gauge(
    "graveboards_build_info",
    "Build information for the Graveboards backend. Always 1; labels identify the version.",
    ["version", "commit"],
)


def set_build_info():
    from app.version import __version__
    commit = _get_commit_hash()
    graveboards_build_info.labels(version=__version__, commit=commit).set(1)


daemon_service_running = Gauge(
    "daemon_service_running",
    "Whether a daemon service is currently running (1) or not (0).",
    ["service"],
)

daemon_jobs_total = Counter(
    "daemon_jobs_total",
    "Total number of daemon jobs executed.",
    ["service", "status"],
)

daemon_job_duration_seconds = Histogram(
    "daemon_job_duration_seconds",
    "Duration of daemon job executions in seconds.",
    ["service"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

daemon_last_job_timestamp = Gauge(
    "daemon_last_job_timestamp",
    "Timestamp of the last successful daemon job execution (Unix epoch).",
    ["service"],
)

daemon_active_jobs = Gauge(
    "daemon_active_jobs",
    "Number of currently active daemon jobs.",
    ["service"],
)
