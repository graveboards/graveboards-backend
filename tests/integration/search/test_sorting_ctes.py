"""
Test sorting CTE factory.

This module contains tests for the sorting CTE factory.
"""

import pytest

pytestmark = [pytest.mark.integration]


@pytest.mark.integration
def test_sorting_schema_structure():
    """Test sorting schema structure."""
    from app.search.datastructures import SortingSchema
    from app.search.enums import ModelField, SortingOrder

    from app.search.datastructures.sorting import SortingOption

    sorting_schema = SortingSchema(
        [
            SortingOption(field=ModelField.BEATMAPSETSNAPSHOT__RANKED, order=SortingOrder.DESCENDING),
            SortingOption(field=ModelField.BEATMAPSETSNAPSHOT__TITLE, order=SortingOrder.ASCENDING),
        ]
    )
    assert len(sorting_schema) == 2
    items = list(sorting_schema)
    assert items[0].field == ModelField.BEATMAPSETSNAPSHOT__RANKED
    assert items[0].order == SortingOrder.DESCENDING
    assert items[1].field == ModelField.BEATMAPSETSNAPSHOT__TITLE
    assert items[1].order == SortingOrder.ASCENDING


@pytest.mark.integration
def test_sorting_schema_empty():
    """Test empty sorting schema."""
    from app.search.datastructures import SortingSchema

    sorting_schema = SortingSchema([])
    assert len(sorting_schema) == 0


@pytest.mark.integration
def test_sorting_schema_single_field():
    """Test sorting schema with single field."""
    from app.search.datastructures import SortingSchema
    from app.search.enums import ModelField, SortingOrder

    from app.search.datastructures.sorting import SortingOption

    sorting_schema = SortingSchema(
        [SortingOption(field=ModelField.BEATMAPSNAPSHOT__RANKED, order=SortingOrder.ASCENDING)]
    )
    assert len(sorting_schema) == 1
    items = list(sorting_schema)
    assert items[0].field == ModelField.BEATMAPSNAPSHOT__RANKED
    assert items[0].order == SortingOrder.ASCENDING


@pytest.mark.integration
def test_sorting_order_enum():
    """Test sorting order enum values."""
    from app.search.enums import SortingOrder

    assert SortingOrder.ASCENDING.value == "asc"
    assert SortingOrder.DESCENDING.value == "desc"


@pytest.mark.integration
def test_sorting_schema_validation():
    """Test sorting schema validation."""
    from app.search.datastructures import SortingSchema
    from app.search.enums import ModelField

    from app.search.datastructures.sorting import SortingOption

    with pytest.raises(Exception):
        SortingSchema([{"invalid": "schema"}])

    with pytest.raises(Exception):
        SortingSchema([SortingOption(field=ModelField.BEATMAPSNAPSHOT__RANKED, order="invalid_order")])


@pytest.mark.integration
def test_sorting_schema_multiple_fields():
    """Test sorting schema with multiple fields."""
    from app.search.datastructures import SortingSchema
    from app.search.enums import ModelField, SortingOrder

    from app.search.datastructures.sorting import SortingOption

    sorting_schema = SortingSchema(
        [
            SortingOption(field=ModelField.BEATMAPSETSNAPSHOT__RANKED, order=SortingOrder.DESCENDING),
            SortingOption(field=ModelField.BEATMAPSETSNAPSHOT__TITLE, order=SortingOrder.ASCENDING),
            SortingOption(field=ModelField.BEATMAPSNAPSHOT__RANKED, order=SortingOrder.ASCENDING),
        ]
    )
    assert len(sorting_schema) == 3
    items = list(sorting_schema)
    assert items[0].field == ModelField.BEATMAPSETSNAPSHOT__RANKED
    assert items[0].order == SortingOrder.DESCENDING
    assert items[1].field == ModelField.BEATMAPSETSNAPSHOT__TITLE
    assert items[1].order == SortingOrder.ASCENDING
    assert items[2].field == ModelField.BEATMAPSNAPSHOT__RANKED
    assert items[2].order == SortingOrder.ASCENDING
