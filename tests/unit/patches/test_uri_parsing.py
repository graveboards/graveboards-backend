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


def test_resolve_query_preserves_deep_object_arrays_and_coerces_filters():
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


def test_resolve_query_coerces_include_booleans_and_json_sorting():
    parser = make_parser()

    assert parser.resolve_query({"include[beatmapset][creator]": ["yes"]}) == {
        "include": {"beatmapset": {"creator": True}}
    }
    assert parser.resolve_query(
        {"sorting": ['{"field":"beatmapset.title","order":"desc"}']}
    ) == {
        "sorting": [{"field": "beatmapset.title", "order": "desc"}]
    }
