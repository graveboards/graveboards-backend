import time

from connexion.middleware.abstract import ROUTING_CONTEXT
from starlette.requests import Request
from starlette.types import ASGIApp, Scope, Receive, Send

from app.observability.logging import get_logger
from .error import errors_total
from .http import http_requests_total, http_request_duration_seconds, http_requests_in_flight

logger = get_logger("app.access")

# Scraped/polled on a tight interval and never interesting on their own;
# still recorded as metrics below, just not logged as access-log noise.
_NOISY_ACCESS_LOG_PATHS = frozenset({"/metrics", "/api/v1/health"})

# Routes registered directly via add_url_rule(), outside the OpenAPI spec, so they
# never get an operation_id from Connexion's routing and would otherwise be
# indistinguishable from genuinely unmatched (404) requests in the endpoint label.
_STATIC_ROUTE_ENDPOINTS = {"/metrics": "metrics"}


def _get_endpoint(scope: Scope) -> str:
    # Connexion resolves routing via its own contextvar/scope-copy mechanism instead
    # of Starlette's usual scope["route"], and stores the match under
    # extensions[ROUTING_CONTEXT]["operation_id"] - the OpenAPI operationId (e.g.
    # "api.v1.beatmaps.get_beatmap"), already parameter-free and low-cardinality by
    # construction, so no path-template regex is needed here.
    operation_id = scope.get("extensions", {}).get(ROUTING_CONTEXT, {}).get("operation_id")
    if operation_id:
        return operation_id

    return _STATIC_ROUTE_ENDPOINTS.get(scope.get("path"), "<unmatched>")


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

        if request.url.path not in _NOISY_ACCESS_LOG_PATHS:
            client_host = request.client.host if request.client else "-"
            client_port = request.client.port if request.client else "-"

            logger.info(
                f"{method} {request.url.path} {client_host}:{client_port} {status_code} {duration:.3f}s"
            )
