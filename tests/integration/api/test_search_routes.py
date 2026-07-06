import pytest
from unittest.mock import AsyncMock

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


class TestSearchHttpIntegration:
    """Integration tests for search HTTP endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_post_returns_201(self, TestClientWithMocks):
        """Test POST /api/v1/search returns 201 with compressed query."""
        from app.search import compress_query

        mock_rc = AsyncMock()

        test_client = TestClientWithMocks(mock_rc=mock_rc)

        response = test_client.post(
            "/api/v1/search",
            json={
                "scope": "beatmaps",
                "search_terms": None,
                "sorting": None,
                "filters": None,
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "q" in data
        assert "message" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_post_invalid_scope_returns_400(self, TestClientWithMocks):
        """Test POST /api/v1/search with invalid scope returns 400."""
        mock_rc = AsyncMock()

        test_client = TestClientWithMocks(mock_rc=mock_rc)

        response = test_client.post(
            "/api/v1/search",
            json={
                "scope": "invalid_scope",
                "search_terms": None,
                "sorting": None,
                "filters": None,
            }
        )

        assert response.status_code == 400
