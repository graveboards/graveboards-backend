from prometheus_client import CollectorRegistry


REGISTRY = CollectorRegistry()


def get_registry() -> CollectorRegistry:
    return REGISTRY
