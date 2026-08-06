"""Prometheus metrics registry singleton."""

from __future__ import annotations

from prometheus_client import REGISTRY

__all__ = ["REGISTRY"]
