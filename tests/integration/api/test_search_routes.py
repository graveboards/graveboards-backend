import pytest

from app.search.datastructures import SearchSchema
from app.search.enums import Scope


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_schema_creation():
    search_query = SearchSchema(
        scope=Scope.BEATMAPS,
        search_terms=None,
        sorting=None,
        filters=None
    )
    
    assert search_query.scope == Scope.BEATMAPS
    assert search_query.search_terms is None
    assert search_query.sorting is None
    assert search_query.filters is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_schema_all_scopes():
    scopes = [Scope.BEATMAPS, Scope.BEATMAPSETS, Scope.QUEUES, Scope.REQUESTS]
    
    for scope in scopes:
        search_query = SearchSchema(
            scope=scope,
            search_terms=None,
            sorting=None,
            filters=None
        )
        assert search_query.scope == scope


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_query_serialization():
    search_query = SearchSchema(
        scope=Scope.BEATMAPSETS,
        search_terms=None,
        sorting=None,
        filters=None
    )
    
    serialized = search_query.serialize()
    
    assert serialized is not None
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_query_deserialization():
    search_query = SearchSchema(
        scope=Scope.BEATMAPSETS,
        search_terms=None,
        sorting=None,
        filters=None
    )
    
    serialized = search_query.serialize()
    deserialized = SearchSchema.deserialize(serialized)
    
    assert deserialized.scope == search_query.scope


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compress_decompress_roundtrip():
    search_query = SearchSchema(
        scope=Scope.BEATMAPS,
        search_terms=None,
        sorting=None,
        filters=None
    )
    
    serialized = search_query.serialize()
    
    from app.search import compress_query, decompress_query
    compressed = compress_query(serialized)
    decompressed = decompress_query(compressed)
    
    assert decompressed == serialized
