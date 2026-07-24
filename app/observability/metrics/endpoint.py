from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response


async def metrics_endpoint(request: Request) -> Response:
    content = generate_latest().decode("utf-8")
    return Response(
        content=content,
        media_type=CONTENT_TYPE_LATEST,
    )
