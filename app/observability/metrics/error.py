from prometheus_client import Counter


errors_total = Counter(
    "errors_total",
    "Total number of errors.",
    ["error_type", "endpoint"],
)
