import time

from starlette.requests import Request
from starlette.types import ASGIApp, Scope, Receive, Send

from .http_metrics import http_requests_total, http_request_duration_seconds, http_requests_in_flight
from .request_id import generate_request_id, set_request_id
from .error_metrics import errors_total


def _get_endpoint(scope: Scope) -> str:
    route = scope.get("route")
    if route is not None:
        return getattr(route, "path", scope.get("path", "/"))
    return scope.get("path", "/")


def clear_request_id() -> None:
    from .request_id import request_id_var
    request_id_var.set(None)


class MetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = generate_request_id()
        set_request_id(request_id)

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
                status_code=str(status_code),
            ).observe(duration)

            http_requests_in_flight.labels(method=method, endpoint=endpoint).dec()

            errors_total.labels(
                error_type=type(exc).__name__,
                endpoint=endpoint,
                status_code=str(status_code),
            ).inc()

            clear_request_id()
            raise

        clear_request_id()

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
            status_code=str(status_code),
        ).observe(duration)

        http_requests_in_flight.labels(method=method, endpoint=endpoint).dec()
