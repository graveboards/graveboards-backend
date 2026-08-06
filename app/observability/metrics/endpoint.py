"""Prometheus metrics endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

if TYPE_CHECKING:
    from starlette.requests import Request


async def metrics_endpoint(_request: Request) -> Response:
    """Expose Prometheus metrics in the OpenMetrics text format.

    Args:
        _request:
            The incoming request (unused).

    Returns:
        The metrics response.
    """
    content = generate_latest().decode("utf-8")
    return Response(
        content=content,
        media_type=CONTENT_TYPE_LATEST,
    )
