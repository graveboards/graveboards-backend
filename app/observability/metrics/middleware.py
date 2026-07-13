import json
import re
import time
from urllib.parse import parse_qsl

from connexion.middleware.abstract import ROUTING_CONTEXT
from starlette.requests import Request
from starlette.types import ASGIApp, Scope, Receive, Send

from app.observability.logging import get_logger
from .error import errors_total
from .http import http_requests_total, http_request_duration_seconds, http_requests_in_flight

logger = get_logger("app.access")

# Scraped/polled on a tight interval and never interesting on their own;
# still recorded as metrics below, just not logged as access-log noise.
_NOISY_ACCESS_LOG_PATHS = frozenset({"/metrics", "/api/v1/health"})

# Routes registered directly via add_url_rule(), outside the OpenAPI spec, so they
# never get an operation_id from Connexion's routing and would otherwise be
# indistinguishable from genuinely unmatched (404) requests in the endpoint label.
_STATIC_ROUTE_ENDPOINTS = {"/metrics": "metrics"}

# Field names (checked case-insensitively, dot/underscore/hyphen-agnostic via a
# plain lowercase match on the key as-is) that never get logged verbatim, in
# either query params or request bodies - auth material and credentials.
_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "pwd",
    "token", "access_token", "refresh_token", "id_token",
    "secret", "client_secret",
    "api_key", "apikey", "x-api-key",
    "authorization",
    "code",  # OAuth authorization code - single-use bearer credential
    "csrf", "csrf_token",
})
_REDACTED = "***REDACTED***"

# Only buffer+replay bodies for methods that carry one, small enough to be an
# API payload rather than an upload, and shaped like something we can parse.
# Anything outside this (multipart uploads, missing/streamed Content-Length,
# oversized payloads, unrecognized content types) is deliberately left
# untouched - the raw ASGI stream is never buffered, so large/streamed
# uploads are unaffected.
_BODY_LOGGABLE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_BODY_LOGGABLE_CONTENT_TYPES = frozenset({"application/json", "application/x-www-form-urlencoded"})
_MAX_LOGGED_BODY_BYTES = 8192


def _get_endpoint(scope: Scope) -> str:
    # Connexion resolves routing via its own contextvar/scope-copy mechanism instead
    # of Starlette's usual scope["route"], and stores the match under
    # extensions[ROUTING_CONTEXT]["operation_id"] - the OpenAPI operationId (e.g.
    # "api.v1.beatmaps.get_beatmap"), already parameter-free and low-cardinality by
    # construction, so no path-template regex is needed here.
    operation_id = scope.get("extensions", {}).get(ROUTING_CONTEXT, {}).get("operation_id")
    if operation_id:
        return operation_id

    return _STATIC_ROUTE_ENDPOINTS.get(scope.get("path"), "<unmatched>")


def _redact(value):
    if isinstance(value, dict):
        return {k: (_REDACTED if k.lower() in _SENSITIVE_KEYS else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _get_query_params(request: Request) -> dict:
    params = {}
    for key in request.query_params.keys():
        values = request.query_params.getlist(key)
        params[key] = values[0] if len(values) == 1 else values
    params = _reconstruct_nested_params(params)
    params = _try_parse_sorting(params)
    return _redact(params)


def _reconstruct_nested_params(params: dict) -> dict:
    """Rebuild flat bracket-notation query params (e.g. ``filters[comment][neq]``)
    into nested dicts so access logs show clean structure instead of a wall of
    dotted field names.

    Keys that don't match the bracket pattern are left untouched. Duplicate
    paths are merged (e.g. ``include[queue][id]`` + ``include[queue][name]``
    become one ``include.queue`` object).
    """
    bracket_re = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)((?:\[[^\]]+\])+)$")
    nested = {}
    flat_keys = []

    for key, value in params.items():
        match = bracket_re.match(key)
        if not match:
            flat_keys.append(key)
            continue

        root = match.group(1)
        raw_segments = match.group(2).replace("[", ".").replace("]", "").split(".")
        segments = [s for s in raw_segments if s]

        if root not in nested:
            nested[root] = {}

        target = nested[root]
        for i, segment in enumerate(segments):
            if i == len(segments) - 1:
                target[segment] = value
            else:
                if segment not in target or not isinstance(target[segment], dict):
                    target[segment] = {}
                target = target[segment]

    for key in flat_keys:
        nested[key] = params[key]

    return nested


def _try_parse_sorting(params: dict) -> dict:
    """The frontend serializes each sort item as JSON.stringify(obj) and sends them
    as repeated query params, so the backend sees strings like
    '{\"field\":\"Request.id\",\"order\":\"asc\"}'. Parse them back into proper
    objects so access logs stay readable instead of showing nested quoted JSON.

    If parsing fails for any reason the original string is kept as fallback.
    """
    if "sorting" not in params:
        return params

    raw = params["sorting"]

    if isinstance(raw, str):
        try:
            params["sorting"] = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    elif isinstance(raw, list):
        parsed = []
        for item in raw:
            if isinstance(item, str):
                try:
                    parsed.append(json.loads(item))
                    continue
                except (json.JSONDecodeError, TypeError):
                    pass
            parsed.append(item)
        params["sorting"] = parsed

    return params


def _parse_body(raw: bytes, content_type: str):
    if not raw:
        return None
    try:
        if content_type == "application/json":
            return _redact(json.loads(raw))
        if content_type == "application/x-www-form-urlencoded":
            return _redact(dict(parse_qsl(raw.decode())))
    except Exception:
        return "<unparseable>"
    return None


async def _capture_body(receive: Receive) -> tuple[bytes, Receive]:
    """Drain the ASGI body stream into memory, returning the bytes plus a
    replacement `receive` that replays the exact same messages so downstream
    body parsing (Connexion's request validation/handler) is unaffected."""
    messages = []
    chunks = []
    more_body = True

    while more_body:
        message = await receive()
        messages.append(message)
        if message["type"] != "http.request":
            break
        chunks.append(message.get("body", b""))
        more_body = message.get("more_body", False)

    async def replay_receive():
        if messages:
            return messages.pop(0)
        return await receive()

    return b"".join(chunks), replay_receive


def _get_auth_info(scope: Scope, request: Request) -> tuple[int | None, str]:
    if request.headers.get("authorization", "").lower().startswith("bearer "):
        auth_scheme = "bearer"
    elif request.headers.get("x-api-key"):
        auth_scheme = "api_key"
    else:
        auth_scheme = "none"

    # Connexion's SecurityMiddleware writes {"user": <sub>, "token_info": {...}}
    # into scope["extensions"]["connexion_context"] once security passes (see
    # connexion.security.SecurityHandlerFactory.verify_security). That dict is
    # mutated in place on the same `scope` object this middleware already holds,
    # so it's readable here with no extra JWT decode or DB lookup - it's simply
    # absent (None) if auth failed or the route has no security requirement.
    connexion_context = scope.get("extensions", {}).get("connexion_context", {})
    user_id = connexion_context.get("user")

    return user_id, auth_scheme


class MetricsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

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

        body_bytes = None
        body_captured = False
        effective_receive = receive

        if method in _BODY_LOGGABLE_METHODS:
            content_length = request.headers.get("content-length")
            content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()

            if (
                content_type in _BODY_LOGGABLE_CONTENT_TYPES
                and content_length is not None
                and content_length.isdigit()
                and int(content_length) <= _MAX_LOGGED_BODY_BYTES
            ):
                body_bytes, effective_receive = await _capture_body(receive)
                body_captured = True
                # `request` was constructed with the original `receive`; rebind it
                # to the replay wrapper so downstream (and this middleware, if it
                # ever reads the body itself) sees the same bytes back.
                request = Request(scope, effective_receive)

        try:
            await self.app(scope, effective_receive, wrapped_send)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            status_code = 500

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            http_requests_in_flight.labels(method=method, endpoint=endpoint).dec()

            errors_total.labels(
                error_type=type(exc).__name__,
                endpoint=endpoint,
            ).inc()

            raise

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
        ).observe(duration)

        http_requests_in_flight.labels(method=method, endpoint=endpoint).dec()

        if request.url.path not in _NOISY_ACCESS_LOG_PATHS:
            client_host = request.client.host if request.client else "-"
            client_port = request.client.port if request.client else "-"
            user_id, auth_scheme = _get_auth_info(scope, request)

            extra_fields: dict = {"user_id": user_id, "auth_scheme": auth_scheme}

            query_params = _get_query_params(request)
            if query_params:
                extra_fields["query_params"] = query_params

            if body_captured:
                content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
                parsed_body = _parse_body(body_bytes, content_type)
                if parsed_body is not None:
                    extra_fields["body"] = parsed_body
            elif method in _BODY_LOGGABLE_METHODS and request.headers.get("content-length") not in (None, "0"):
                extra_fields["body"] = "<not captured: too large or unsupported content-type>"

            logger.info(
                f"{method} {request.url.path} {client_host}:{client_port} {status_code} {duration:.3f}s",
                **extra_fields,
            )
