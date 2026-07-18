from prometheus_client import Counter


auth_rate_limit_checks_total = Counter(
    "auth_rate_limit_checks_total",
    "Total number of auth rate-limit checks.",
    ["result"],  # allowed | rate_limited | locked_out
)

auth_lockouts_total = Counter(
    "auth_lockouts_total",
    "Total number of IPs locked out for excessive auth failures.",
)
