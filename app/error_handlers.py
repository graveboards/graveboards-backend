from connexion.problem import problem
from connexion.exceptions import Forbidden, BadRequestProblem, Unauthorized, InternalServerError
from connexion.lifecycle import ConnexionRequest, ConnexionResponse

from app.observability.metrics.error import errors_total


def _track_error(request: ConnexionRequest, status_code: int, error_type: str) -> None:
    try:
        endpoint = request.url.path
    except Exception:
        endpoint = "unknown"

    errors_total.labels(
        error_type=error_type,
        endpoint=endpoint,
    ).inc()


def forbidden(request: ConnexionRequest, exc: Exception | Forbidden) -> ConnexionResponse:
    _track_error(request, 403, "forbidden")
    return problem(status=403, title="Forbidden", detail=exc.detail, type="about:blank")


def bad_request(request: ConnexionRequest, exc: Exception | BadRequestProblem) -> ConnexionResponse:
    _track_error(request, 400, "bad_request")
    return problem(status=400, title="Bad Request", detail=str(exc), type="about:blank")


def unauthorized(request: ConnexionRequest, exc: Exception | Unauthorized) -> ConnexionResponse:
    _track_error(request, 401, "unauthorized")
    return problem(status=401, title="Unauthorized", detail=str(exc), type="about:blank")


def internal_error(request: ConnexionRequest, exc: Exception | InternalServerError) -> ConnexionResponse:
    _track_error(request, 500, "internal_server_error")
    return problem(status=500, title="Internal Server Error", detail="An unexpected error occurred", type="about:blank")
