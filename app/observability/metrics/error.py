from prometheus_client import Counter
from .registry import REGISTRY


errors_total = Counter(
    "errors_total",
    "Total number of errors.",
    ["error_type", "endpoint"],
    registry=REGISTRY,
)
