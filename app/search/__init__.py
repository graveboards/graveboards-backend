__all__ = [
    "compress_query",
    "decompress_query",
    "SearchEngine",
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
    "Scope",
    "ScopeLiteral",
    "SortingOrder",
    "SortingOrderId",
    "ModelField",
    "ModelFieldId",
    "SearchableFieldCategory",
    "SearchableFieldCategoryFlag",
    "CATEGORY_NAMES",
    "SCOPE_MODEL_MAPPING",
    "SCOPE_SCHEMA_MAPPING",
    "SCOPE_OPTIONS_MAPPING",
    "SCOPE_CATEGORIES_MAPPING",
    "CATEGORY_MODEL_FIELDS_MAPPING",
    "CATEGORY_FIELD_GROUPS_MAPPING",
]


def __getattr__(name):
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
