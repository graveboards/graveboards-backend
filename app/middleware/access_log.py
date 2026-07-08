import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("app.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request in the same format as application logs.

    Outputs:  {asctime} | {levelname:<8} | {alias:<8} | [HTTP] {method} {path} {status} {duration}s

    In dev this uses the colored LogFormatter (same as all app logs).
    In prod this uses JSONLogFormatter (same as all app logs).

    Includes method, path, status code, duration, and request_id via the
    shared logging context.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        client_host = request.client.host if request.client else "-"
        client_port = request.client.port if request.client else "-"

        logger.info(
            "%s %s %s:%s %d %.3fs",
            request.method,
            request.url.path,
            client_host,
            client_port,
            response.status_code,
            duration,
            extra={"prefix": "HTTP"},
        )
        return response
