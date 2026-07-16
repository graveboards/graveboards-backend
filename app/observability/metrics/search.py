from prometheus_client import Counter, Histogram


search_requests_total = Counter(
    "search_requests_total",
    "Total number of search requests.",
    ["scope", "mode", "cached"],
)

search_duration_seconds = Histogram(
    "search_duration_seconds",
    "Search query duration in seconds.",
    ["scope", "mode", "cached"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

search_cache_hits_total = Counter(
    "search_cache_hits_total",
    "Total number of search cache hits.",
    ["scope"],
)

search_cache_misses_total = Counter(
    "search_cache_misses_total",
    "Total number of search cache misses.",
    ["scope"],
)
