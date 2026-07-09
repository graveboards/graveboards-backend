from prometheus_client import (
    CollectorRegistry,
    PlatformCollector,
    ProcessCollector,
)


REGISTRY = CollectorRegistry()

ProcessCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)


def get_registry() -> CollectorRegistry:
    return REGISTRY
