from prometheus_client import Counter
from .registry import REGISTRY


rate_limit_attempts_total = Counter(
    "rate_limit_attempts_total",
    "Total number of rate limit check attempts.",
    ["endpoint", "result"],
    registry=REGISTRY,
)

rate_limit_retries_total = Counter(
    "rate_limit_retries_total",
    "Total number of rate limit retry attempts.",
    ["endpoint"],
    registry=REGISTRY,
)
