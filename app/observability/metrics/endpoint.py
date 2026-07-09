from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


async def metrics_endpoint(request):
    content = generate_latest().decode("utf-8")
    return Response(
        content=content,
        media_type=CONTENT_TYPE_LATEST,
    )
