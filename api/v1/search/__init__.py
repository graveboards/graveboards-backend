import json
import time

from sqlalchemy import func, select as sa_select

from connexion import request
from connexion.exceptions import Unauthorized

from api.auth import bearer_info, api_key_info
from api.pagination import build_pagination_response
from api.utils import pop_auth_info
from app.patches.validators import validate_include
from app.database import PostgresqlDB
from app.database.queue_access import queue_visibility_where
from app.redis import RedisClient
from app.exceptions import (
    FieldValidationError,
    FieldNotSupportedError,
    FieldConditionValidationError,
    UnknownFieldCategoryError,
    AllValuesNullError,
    DeepObjectValidationError,
    bad_request_factory
)
from app.search import compress_query, decompress_query, SearchSchema, SearchEngine, Scope, SCOPE_MODEL_MAPPING
from app.search.cache import SearchCache
from app.observability.metrics.search import (
    search_requests_total,
    search_duration_seconds,
    search_cache_hits_total,
    search_cache_misses_total,
)
from app.spec import get_include_schema

__all__ = ["search", "post"]

EXCEPTIONS = (
    ValueError,
    TypeError,
    FieldValidationError,
    FieldNotSupportedError,
    FieldConditionValidationError,
    UnknownFieldCategoryError,
    AllValuesNullError,
    DeepObjectValidationError
)

# Scopes whose dedicated endpoints (GET /queues, GET /requests) require auth. This
# route has no OpenAPI `security` block - beatmaps/beatmapsets/scores/profiles are
# meant to stay publicly searchable - so connexion never validates a token for it.
# Scopes backed by auth-required resources need a manual check here instead, or
# they'd be reachable anonymously through search even though their direct endpoints
# require a token.
SCOPES_REQUIRING_AUTH = frozenset({Scope.QUEUES, Scope.REQUESTS})


async def _authenticate_for_scope(scope: Scope) -> int | None:
    """Manually validate the caller's token for scopes that require auth.

    Returns the authenticated user ID, or ``None`` if the scope doesn't require
    auth. Raises ``Unauthorized`` if the scope requires auth and no valid
    Bearer token or API key is present.
    """
    if scope not in SCOPES_REQUIRING_AUTH:
        return None

    auth_header = request.headers.get("authorization", "")
    api_key_header = request.headers.get("x-api-key")

    token_info = None

    if auth_header.lower().startswith("bearer "):
        token_info = await bearer_info(auth_header[len("bearer "):].strip(), request)
    elif api_key_header:
        token_info = await api_key_info(api_key_header, request)

    if token_info is None:
        raise Unauthorized(f"Authentication is required to search scope '{scope.value}'")

    return int(token_info["sub"])


async def search(**kwargs):
    db: PostgresqlDB = request.state.db
    rc: RedisClient = request.state.rc

    pop_auth_info(kwargs)

    start_time = time.perf_counter()
    cached = False

    try:
        compressed = kwargs.pop("compressed", False)
        include = kwargs.pop("include", None)
        reversed_ = kwargs.pop("reversed", None)

        if compressed:
            q = decompress_query(kwargs.pop("q"))
            sq = SearchSchema.deserialize(q)
        else:
            q = json.loads(kwargs.pop("q"))
            sq = SearchSchema.model_validate(q)

        caller_user_id = await _authenticate_for_scope(sq.scope)

        validate_include(include, get_include_schema(SCOPE_MODEL_MAPPING[sq.scope]))

        limit = kwargs.get("limit", 50)
        offset = kwargs.get("offset", 0)

        cache = SearchCache(rc)
        sorting_str = json.dumps(sq.sorting) if sq.sorting else ""
        filters_str = json.dumps(sq.filters) if sq.filters else ""

        # Skip the cache for queues, since results depend on the caller's identity
        # (owner/manager visibility) and not just the query parameters.
        cached_result = await cache.get(
            scope=sq.scope,
            search_terms=sq.search_terms.terms if sq.search_terms else "",
            sorting=sorting_str,
            filters=filters_str,
            limit=limit,
            offset=offset,
        ) if sq.scope is not Scope.QUEUES else None

        if cached_result:
            cached = True
            page_data = cached_result["data"]
            total = cached_result["total"]
            search_cache_hits_total.labels(scope=sq.scope.value).inc()
        else:
            se = SearchEngine(sq.scope, search_terms=sq.search_terms, sorting=sq.sorting, filters=sq.filters)

            if sq.scope is Scope.QUEUES:
                se.query = se.query.where(queue_visibility_where(caller_user_id))

            async with db.session() as session:
                page = await se.search(session, limit=limit, offset=offset)
                count_query = sa_select(func.count()).select_from(se.query.subquery())
                total = await session.scalar(count_query)

            page_data = se.dump(page, include=include)

            if reversed_:
                page_data.reverse()

            if sq.scope is not Scope.QUEUES:
                cache_entry = {"data": page_data, "total": total}
                await cache.set(
                    scope=sq.scope,
                    search_terms=sq.search_terms.terms if sq.search_terms else "",
                    sorting=sorting_str,
                    filters=filters_str,
                    limit=limit,
                    offset=offset,
                    page_data=cache_entry,
                )

            search_cache_misses_total.labels(scope=sq.scope.value).inc()
    except EXCEPTIONS as e:
        raise bad_request_factory(e)

    request_url = str(request.url)
    page_data, status, headers = build_pagination_response(
        data=page_data,
        total=total,
        limit=limit,
        offset=offset,
        request_url=request_url,
    )

    duration = time.perf_counter() - start_time
    search_duration_seconds.labels(
        scope=sq.scope.value,
        mode="query",
        cached="true" if cached else "false",
    ).observe(duration)
    search_requests_total.labels(
        scope=sq.scope.value,
        mode="query",
        cached="true" if cached else "false",
    ).inc()

    return page_data, status, headers


async def post(body: dict):
    rc: RedisClient = request.state.rc  # TODO: caching

    try:
        search_query = SearchSchema.model_validate(body)
        q = compress_query(search_query.serialize())
    except EXCEPTIONS as e:
        raise bad_request_factory(e)

    return {"message": "Search resource created successfully", "q": q}, 201, {"Content-Type": "application/json"}
