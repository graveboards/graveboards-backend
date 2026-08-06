"""Re-exports for OpenAPI spec loading."""

from __future__ import annotations

from typing import Any

__all__ = ["get_filter_schema", "get_include_schema", "load_spec"]


def __getattr__(name: str) -> Any:
    if name == "load_spec":
        from .load import load_spec

        return load_spec

    if name in {"get_filter_schema", "get_include_schema"}:
        from . import schema

        return getattr(schema, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
