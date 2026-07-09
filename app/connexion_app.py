import os

from connexion import AsyncApp
from connexion.exceptions import Forbidden, BadRequestProblem, Unauthorized, InternalServerError
from connexion.resolver import RestyResolver
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .lifespan import lifespan
from .logging import setup_logging
from .observability.metrics.endpoint import metrics_endpoint
from .observability.metrics.middleware import MetricsMiddleware
from .observability.context import RequestContextMiddleware
from .patches import OpenAPIURIParserPatched, ParameterValidatorPatched
from .spec import load_spec
from .error_handlers import forbidden, bad_request, unauthorized, internal_error
from .config import SPEC_DIR, DEFAULT_MODULE_NAME, INSTANCE_DIR, ENV, DISABLE_SECURITY
from .enums import Env


def create_connexion_app() -> AsyncApp:
    # Configure logging here, before uvicorn's config.load() returns and it emits
    # its first startup lines ("Started server process", etc.), so those render
    # through our handlers too rather than uvicorn's stock format.
    setup_logging()

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    if DISABLE_SECURITY and ENV is not Env.DEV:
        raise RuntimeError(
            "DISABLE_SECURITY=True is not allowed outside of dev environments. "
            "Set ENV=dev or remove DISABLE_SECURITY from your environment."
        )

    connexion_app = AsyncApp(
        __name__,
        specification_dir=SPEC_DIR,
        lifespan=lifespan,
        uri_parser_class=OpenAPIURIParserPatched,  # type: ignore
        validator_map={
            "parameter": ParameterValidatorPatched
        }
    )

    connexion_app.add_middleware(RequestContextMiddleware, position=MiddlewarePosition.BEFORE_ROUTING)
    connexion_app.add_middleware(
        MetricsMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
    )

    # TODO: Restrict CORS to known frontend domains before production deployment
    connexion_app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    connexion_app.add_middleware(
        GZipMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION
    )

    connexion_app.add_api(
        load_spec(),
        resolver=RestyResolver(DEFAULT_MODULE_NAME)
    )

    connexion_app.add_error_handler(Forbidden, forbidden)
    connexion_app.add_error_handler(BadRequestProblem, bad_request)
    connexion_app.add_error_handler(Unauthorized, unauthorized)
    connexion_app.add_error_handler(InternalServerError, internal_error)

    connexion_app.add_url_rule("/metrics", "metrics", metrics_endpoint, methods=["GET"])

    return connexion_app
