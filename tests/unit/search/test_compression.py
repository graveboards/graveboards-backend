import pytest

from app.search.compression import compress_query, decompress_query


pytestmark = pytest.mark.unit


def test_compress_query_round_trips_structured_search_payload():
    payload = {
        "scope": "beatmaps",
        "search_terms": {
            "artist": ["Camellia"],
            "title": ["crystallized"],
        },
        "filters": {
            "beatmap": {
                "star_rating": {"gte": 5.2, "lt": 7},
                "ranked": True,
            }
        },
        "sorting": [{"field": "beatmapset.title", "order": "asc"}],
    }

    compressed = compress_query(payload, serialized=False)

    assert isinstance(compressed, str)
    assert "=" not in compressed
    assert decompress_query(compressed, serialized=False) == payload


def test_decompress_query_rejects_truncated_or_non_query_data():
    compressed = compress_query(b'{"scope":"beatmaps"}')

    with pytest.raises(ValueError, match="Could not decompress query"):
        decompress_query(compressed[:-3])

    with pytest.raises(TypeError, match="q must be str"):
        decompress_query(b"not-a-string")
