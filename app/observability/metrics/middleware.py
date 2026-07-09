import time

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp, Scope, Receive, Send

from app.observability.logging import get_logger
from .error import errors_total
from .http import http_requests_total, http_request_duration_seconds, http_requests_in_flight

logger = get_logger("app.access")


def _get_endpoint(scope: Scope) -> str:
    route = scope.get("route")
    if route is not None:
        path = getattr(route, "path", None)
        if path is not None:
            return path
    return "<unmatched>"


class MetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        method = request.method
        endpoint = _get_endpoint(scope)

        http_requests_in_flight.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()
        status_code_ref: dict = {"value": None}

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_code_ref["value"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            status_code = 500

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            http_requests_in_flight.labels(method=method, endpoint=endpoint).dec()

            errors_total.labels(
                error_type=type(exc).__name__,
                endpoint=endpoint,
            ).inc()

            raise

        status_code = status_code_ref["value"]
        if status_code is None:
            status_code = 200

        duration = time.perf_counter() - start_time

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

        http_requests_in_flight.labels(method=method, endpoint=endpoint).dec()

        client_host = request.client.host if request.client else "-"
        client_port = request.client.port if request.client else "-"

        logger.info(
            f"{method} {request.url.path} {client_host}:{client_port} {status_code} {duration:.3f}s"
        )
