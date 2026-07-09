from prometheus_client import Counter, Gauge, Histogram
from .registry import REGISTRY


http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests.",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

http_requests_in_flight = Gauge(
    "http_requests_in_flight",
    "Number of HTTP requests currently being processed.",
    ["method", "endpoint"],
    registry=REGISTRY,
)
