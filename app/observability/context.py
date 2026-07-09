import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Generate or propagate a request_id, bind it to structlog contextvars, and echo it in the response.

    If the incoming request includes an X-Request-ID header, that value is used.
    Otherwise a random 32-char hex ID is generated.

    The ID is bound to structlog contextvars so every log line emitted during the
    request automatically includes it. It is also echoed back in the X-Request-ID
    response header for correlation.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_contextvars()
