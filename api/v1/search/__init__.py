import json

from connexion import request

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
    IncludeValidationError,
    bad_request_factory
)
from app.search import compress_query, decompress_query, SearchSchema, SearchEngine, SCOPE_MODEL_MAPPING
from app.spec import get_include_schema

EXCEPTIONS = (
    ValueError,
    TypeError,
    FieldValidationError,
    FieldNotSupportedError,
    FieldConditionValidationError,
    UnknownFieldCategoryError,
    AllValuesNullError,
    IncludeValidationError
)


async def search(**kwargs):
    db: PostgresqlDB = request.state.db
    rc: RedisClient = request.state.rc

    pop_auth_info(kwargs)

    try:
        compressed = kwargs.pop("compressed", False)
        include = kwargs.pop("include", None)

        if compressed:
            q = decompress_query(kwargs.pop("q"))
            sq = SearchSchema.deserialize(q)
        else:
            q = json.loads(kwargs.pop("q"))
            sq = SearchSchema.model_validate(q)

        validate_include(include, get_include_schema(SCOPE_MODEL_MAPPING[sq.scope]))

        se = SearchEngine(sq.scope, search_terms=sq.search_terms, sorting=sq.sorting, filters=sq.filters)

        async with db.session() as session:
            page = await se.search(session, **kwargs, debug=True)
    except EXCEPTIONS as e:
        raise bad_request_factory(e)

    page_data = se.dump(page, include=include)

    return page_data, 200, {"Content-Type": "application/json"}


async def post(body: dict):
    rc: RedisClient = request.state.rc  # TODO: caching

    try:
        search_query = SearchSchema.model_validate(body)
        q = compress_query(search_query.serialize())
    except EXCEPTIONS as e:
        raise bad_request_factory(e)

    return {"message": "Search resource created successfully", "q": q}, 201, {"Content-Type": "application/json"}
