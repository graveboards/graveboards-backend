"""Re-exports for the osu! API client."""

from __future__ import annotations

from typing import Any

__all__ = ["OsuAPIClient"]


def __getattr__(name: str) -> Any:
    if name == "OsuAPIClient":
        from .osu_api_client import OsuAPIClient

        return OsuAPIClient

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
