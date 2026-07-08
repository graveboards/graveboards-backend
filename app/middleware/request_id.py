import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate or propagate a request ID for the lifetime of each request.

    If the incoming request includes an X-Request-ID header, that value is used.
    Otherwise a random 12-char hex ID is generated.

    The ID is stored in a contextvar so all loggers in the request chain can
    access it via get_request_id(), and it is echoed back in the response header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        from app.metrics.request_id import set_request_id

        set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
