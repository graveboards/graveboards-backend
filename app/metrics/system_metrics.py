from prometheus_client import Counter, Gauge
from .registry import REGISTRY


process_cpu_seconds_total = Counter(
    "process_cpu_seconds_total",
    "Total user and system CPU time spent in seconds.",
    registry=REGISTRY,
)

process_resident_memory_bytes = Gauge(
    "process_resident_memory_bytes",
    "Current resident memory size in bytes.",
    registry=REGISTRY,
)

process_virtual_memory_bytes = Gauge(
    "process_virtual_memory_bytes",
    "Current virtual memory size in bytes.",
    registry=REGISTRY,
)

process_start_time_seconds = Gauge(
    "process_start_time_seconds",
    "Start time of the process since unix epoch in seconds.",
    registry=REGISTRY,
)
