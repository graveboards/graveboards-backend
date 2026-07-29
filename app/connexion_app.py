from __future__ import annotations
import os

from connexion import AsyncApp
from connexion.exceptions import BadRequestProblem, Forbidden, InternalServerError, Unauthorized
from connexion.middleware import MiddlewarePosition
from connexion.resolver import RestyResolver
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .config import DEFAULT_MODULE_NAME, DISABLE_SECURITY, ENV, INSTANCE_DIR, SPEC_DIR
from .database.rules.exceptions import RuleViolationError
from .enums import Env
from .error_handlers import bad_request, forbidden, internal_error, rule_violation, unauthorized
from .lifespan import lifespan
from .observability.context import RequestContextMiddleware
from .observability.logging import setup_logging
from .observability.metrics.endpoint import metrics_endpoint
from .observability.metrics.middleware import MetricsMiddleware
from .patches import OpenAPIURIParserPatched, ParameterValidatorPatched
from .spec import load_spec


def create_connexion_app() -> AsyncApp:
    # Configure logging here, before uvicorn's config.load() returns and it emits
    # its first startup lines ("Started server process", etc.), so those render
    # through our handlers too rather than uvicorn's stock format.
    setup_logging()

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    if DISABLE_SECURITY and ENV.value != Env.DEV.value:
        raise RuntimeError(
            "DISABLE_SECURITY=True is not allowed outside of dev environments. "
            "Set ENV=dev or remove DISABLE_SECURITY from your environment."
        )

    connexion_app = AsyncApp(
        __name__,
        specification_dir=SPEC_DIR,
        lifespan=lifespan,
        uri_parser_class=OpenAPIURIParserPatched,
        validator_map={"parameter": ParameterValidatorPatched},
    )

    # BEFORE_EXCEPTION sits outer to everything below, so request_id stays bound
    # in structlog contextvars for the whole request, including the access log
    # line MetricsMiddleware emits after the handler returns.
    connexion_app.add_middleware(
        RequestContextMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION
    )

    # Must be BEFORE_SECURITY (i.e. after RoutingMiddleware), not BEFORE_EXCEPTION:
    # scope["route"] is only populated once RoutingMiddleware has resolved the
    # request, so reading it any earlier makes the `endpoint` label permanently
    # "<unmatched>". BEFORE_SECURITY still wraps security/validation/the handler,
    # so status codes and exceptions from those stages are captured correctly.
    connexion_app.add_middleware(
        MetricsMiddleware,
        position=MiddlewarePosition.BEFORE_SECURITY,
    )

    # TODO: Restrict CORS to known frontend domains before production deployment
    connexion_app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    connexion_app.add_middleware(GZipMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION)

    connexion_app.add_api(load_spec(), resolver=RestyResolver(DEFAULT_MODULE_NAME))

    connexion_app.add_error_handler(Forbidden, forbidden)
    connexion_app.add_error_handler(BadRequestProblem, bad_request)
    connexion_app.add_error_handler(Unauthorized, unauthorized)
    connexion_app.add_error_handler(InternalServerError, internal_error)
    connexion_app.add_error_handler(RuleViolationError, rule_violation)

    connexion_app.add_url_rule("/metrics", "metrics", metrics_endpoint, methods=["GET"])

    return connexion_app
