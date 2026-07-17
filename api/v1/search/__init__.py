import json
import time

from sqlalchemy import func, select as sa_select

from connexion import request

from api.pagination import build_pagination_response
from api.utils import pop_auth_info
from app.patches.validators import validate_include
from app.database import PostgresqlDB
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
from app.search import compress_query, decompress_query, SearchSchema, SearchEngine, SCOPE_MODEL_MAPPING
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

        validate_include(include, get_include_schema(SCOPE_MODEL_MAPPING[sq.scope]))

        limit = kwargs.get("limit", 50)
        offset = kwargs.get("offset", 0)

        cache = SearchCache(rc)
        sorting_str = json.dumps(sq.sorting) if sq.sorting else ""
        filters_str = json.dumps(sq.filters) if sq.filters else ""

        cached_result = await cache.get(
            scope=sq.scope,
            search_terms=sq.search_terms.terms if sq.search_terms else "",
            sorting=sorting_str,
            filters=filters_str,
            limit=limit,
            offset=offset,
        )

        if cached_result:
            cached = True
            page_data = cached_result["data"]
            total = cached_result["total"]
            search_cache_hits_total.labels(scope=sq.scope.value).inc()
        else:
            se = SearchEngine(sq.scope, search_terms=sq.search_terms, sorting=sq.sorting, filters=sq.filters)

            async with db.session() as session:
                page = await se.search(session, limit=limit, offset=offset)
                count_query = sa_select(func.count()).select_from(se.query.subquery())
                total = await session.scalar(count_query)

            page_data = se.dump(page, include=include)

            if reversed_:
                page_data.reverse()

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
