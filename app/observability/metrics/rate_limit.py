from prometheus_client import Counter


rate_limit_attempts_total = Counter(
    "rate_limit_attempts_total",
    "Total number of rate limit check attempts.",
    ["endpoint", "result"],
)

rate_limit_retries_total = Counter(
    "rate_limit_retries_total",
    "Total number of rate limit retry attempts.",
    ["endpoint"],
)
