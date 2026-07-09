from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .registry import REGISTRY


async def metrics_endpoint(request):
    content = generate_latest(REGISTRY).decode("utf-8")
    return Response(
        content=content,
        media_type=CONTENT_TYPE_LATEST,
    )
