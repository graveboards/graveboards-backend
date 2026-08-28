import pytest

from app.patches.uri_parsing import OpenAPIURIParserPatched

pytestmark = pytest.mark.unit


def make_parser() -> OpenAPIURIParserPatched:
    return OpenAPIURIParserPatched(
        [
            {
                "name": "sorting",
                "in": "query",
                "schema": {"type": "array", "items": {"type": "object"}},
            },
            {
                "name": "filters",
                "in": "query",
                "style": "deepObject",
                "explode": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "beatmap": {
                            "type": "object",
                            "properties": {
                                "ids": {"type": "array", "items": {"type": "integer"}},
                                "ranked": {"type": "boolean"},
                                "difficulty": {
                                    "type": "object",
                                    "properties": {"gte": {"type": "number"}},
                                },
                            },
                        },
                    },
                },
            },
            {
                "name": "include",
                "in": "query",
                "style": "deepObject",
                "explode": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "beatmapset": {
                            "oneOf": [
                                {"type": "boolean"},
                                {
                                    "type": "object",
                                    "properties": {"creator": {"type": "boolean"}},
                                },
                            ],
                        },
                    },
                },
            },
        ],
        {},
    )


def test_resolve_query_preserves_deep_object_arrays_and_coerces_filters() -> None:
    query = {
        "filters[beatmap][ids]": ["1", "2"],
        "filters[beatmap][ranked]": ["true"],
        "filters[beatmap][difficulty][gte]": ["5.6"],
    }

    resolved = make_parser().resolve_query(query)

    assert resolved == {
        "filters": {
            "beatmap": {
                "ids": [1, 2],
                "ranked": True,
                "difficulty": {"gte": 5.6},
            }
        }
    }


def test_resolve_query_coerces_include_booleans_and_json_sorting() -> None:
    parser = make_parser()

    assert parser.resolve_query({"include[beatmapset][creator]": ["yes"]}) == {
        "include": {"beatmapset": {"creator": True}}
    }
    assert parser.resolve_query({"sorting": ['{"field":"beatmapset.title","order":"desc"}']}) == {
        "sorting": [{"field": "beatmapset.title", "order": "desc"}]
    }


@pytest.mark.parametrize(
    "raw_key",
    [
        "include[beatmapset][creator]",  # raw brackets
        "include%5Bbeatmapset%5D%5Bcreator%5D",  # one surviving encoding layer (double-encoded client)
        "include%255Bbeatmapset%255D%255Bcreator%255D",  # two surviving encoding layers
        "include%5Bbeatmapset%5D[creator]",  # mixed encoding
    ],
)
def test_resolve_query_parses_encoded_deep_object_keys(raw_key: str) -> None:
    parser = make_parser()

    resolved = parser.resolve_query({raw_key: ["true"]})

    assert resolved == {"include": {"beatmapset": {"creator": True}}}


def test_resolve_query_encoded_deep_object_keys_survive_partial_encoding() -> None:
    """A client that encodes only some brackets must not swallow path segments.

    Regression: `include%5Bbeatmap_snapshots%5D[accuracy]` used to be parsed as
    `include[accuracy]`, silently dropping the relationship segment.
    """
    parser = make_parser()

    resolved = parser.resolve_query({"filters%5Bbeatmap%5D[ranked]": ["true"]})

    assert resolved == {"filters": {"beatmap": {"ranked": True}}}
