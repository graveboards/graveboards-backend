import json

from connexion import request

from api.utils import pop_auth_info
from app.database import PostgresqlDB
from app.redis import RedisClient
from app.exceptions import (
    FieldValidationError,
    FieldNotSupportedError,
    FieldConditionValidationError,
    UnknownFieldCategoryError,
    AllValuesNullError
)
from app.search import compress_query, decompress_query, SearchSchema, SearchEngine

EXCEPTIONS = (ValueError, TypeError, FieldValidationError, FieldNotSupportedError, FieldConditionValidationError, UnknownFieldCategoryError, AllValuesNullError)


async def search(**kwargs):
    db: PostgresqlDB = request.state.db
    rc: RedisClient = request.state.rc

    pop_auth_info(kwargs)

    try:
        compressed = kwargs.pop("compressed", False)
        frontend_mode = kwargs.pop("frontend_mode", False)

        if compressed:
            q = decompress_query(kwargs.pop("q"))
            sq = SearchSchema.deserialize(q)
        else:
            q = json.loads(kwargs.pop("q"))
            sq = SearchSchema.model_validate(q)

        se = SearchEngine(sq.scope, search_terms=sq.search_terms, sorting=sq.sorting, filters=sq.filters, frontend_mode=frontend_mode)

        async with db.session() as session:
            page = await se.search(session, **kwargs, debug=True)
    except EXCEPTIONS as e:
        return {"message": str(e)}, 400

    page_data = se.dump(page)

    return page_data, 200


async def post(body: dict):
    rc: RedisClient = request.state.rc  # TODO: caching

    try:
        search_query = SearchSchema.model_validate(body)
        q = compress_query(search_query.serialize())
    except EXCEPTIONS as e:
        return {"message": str(e)}, 400

    return {"message": "Search resource created successfully", "q": q}, 201
