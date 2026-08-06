"""Re-exports for search engine and data structures."""

from __future__ import annotations

from typing import Any

__all__ = [
    "CATEGORY_FIELD_GROUPS_MAPPING",
    "CATEGORY_MODEL_FIELDS_MAPPING",
    "CATEGORY_NAMES",
    "SCOPE_CATEGORIES_MAPPING",
    "SCOPE_MODEL_MAPPING",
    "SCOPE_OPTIONS_MAPPING",
    "SCOPE_SCHEMA_MAPPING",
    "ConditionField",
    "ConditionValue",
    "Conditions",
    "FieldFilters",
    "FieldWeights",
    "FiltersSchema",
    "ModelField",
    "ModelFieldId",
    "PatternMultipliers",
    "Scope",
    "ScopeLiteral",
    "SearchEngine",
    "SearchSchema",
    "SearchTermsSchema",
    "SearchableFieldCategory",
    "SearchableFieldCategoryFlag",
    "SortingOption",
    "SortingOrder",
    "SortingOrderId",
    "SortingSchema",
    "compress_query",
    "decompress_query",
]


def __getattr__(name: str) -> Any:
    if name in {"compress_query", "decompress_query"}:
        from . import compression

        return getattr(compression, name)

    if name == "SearchEngine":
        from .engine import SearchEngine

        return SearchEngine

    if name in {
        "SearchSchema",
        "Conditions",
        "ConditionField",
        "ConditionValue",
        "SearchTermsSchema",
        "SortingSchema",
        "SortingOption",
        "FiltersSchema",
        "FieldFilters",
        "FieldWeights",
        "PatternMultipliers",
    }:
        from . import datastructures

        return getattr(datastructures, name)

    if name in {
        "Scope",
        "ScopeLiteral",
        "SortingOrder",
        "SortingOrderId",
        "ModelField",
        "ModelFieldId",
        "SearchableFieldCategory",
        "SearchableFieldCategoryFlag",
        "CATEGORY_NAMES",
    }:
        from . import enums

        return getattr(enums, name)

    if name in {
        "SCOPE_MODEL_MAPPING",
        "SCOPE_SCHEMA_MAPPING",
        "SCOPE_OPTIONS_MAPPING",
        "SCOPE_CATEGORIES_MAPPING",
        "CATEGORY_MODEL_FIELDS_MAPPING",
        "CATEGORY_FIELD_GROUPS_MAPPING",
    }:
        from . import mappings

        return getattr(mappings, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
