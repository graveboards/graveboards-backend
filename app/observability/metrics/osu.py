from prometheus_client import Counter, Histogram
from .registry import REGISTRY


osu_api_requests_total = Counter(
    "osu_api_requests_total",
    "Total number of osu! API requests.",
    ["endpoint", "status_code"],
    registry=REGISTRY,
)

osu_api_request_duration_seconds = Histogram(
    "osu_api_request_duration_seconds",
    "osu! API request duration in seconds.",
    ["endpoint"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

osu_api_errors_total = Counter(
    "osu_api_errors_total",
    "Total number of osu! API errors.",
    ["endpoint", "error_type"],
    registry=REGISTRY,
)
