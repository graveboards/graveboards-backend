import pytest
from unittest.mock import MagicMock, patch

from app.search.datastructures import (
    SearchSchema,
    Conditions,
    ConditionValue,
    SearchTermsSchema,
    SortingSchema,
    SortingOption,
    FiltersSchema,
    FieldFilters,
    FieldWeights,
    PatternMultipliers,
)
from app.search.enums import Scope


class TestDatastructures:
    """Test search data structures."""

    def test_conditions_creation(self):
        """Test Conditions creation."""
        conditions = Conditions(eq=123)

        assert conditions.eq == 123

    def test_conditions_multiple_fields(self):
        """Test Conditions with multiple fields."""
        conditions = Conditions(
            eq=123,
            gt=100,
            lt=200
        )

        assert conditions.eq == 123
        assert conditions.gt == 100
        assert conditions.lte is None

    def test_conditions_shorthand_normalization(self):
        """Test Conditions shorthand normalization."""
        conditions = Conditions.model_validate(42)

        assert conditions.eq == 42

    def test_conditions_none_normalization(self):
        """Test Conditions None normalization."""
        conditions = Conditions.model_validate(None)

        assert conditions.is_null is True

    def test_conditions_validate_keys(self):
        """Test Conditions validates keys."""
        with pytest.raises(Exception):
            Conditions.model_validate({"invalid": 123})

    def test_sorting_option_creation(self):
        """Test SortingOption creation."""
        option = SortingOption(
            field=MagicMock(),
            order="asc"
        )

        assert option.order == "asc"

    def test_sorting_schema_creation(self):
        """Test SortingSchema creation."""
        schema = SortingSchema(root=[
            SortingOption(field=MagicMock())
        ])

        assert len(schema) == 1

    def test_field_filters_creation(self):
        """Test FieldFilters creation."""
        filters = FieldFilters(root={
            "id": Conditions(eq=123)
        })

        assert "id" in filters

    def test_filters_schema_creation(self):
        """Test FiltersSchema creation."""
        schema = FiltersSchema(
            profile=FieldFilters(root={})
        )

        assert schema.profile is not None

    def test_search_schema_creation(self):
        """Test SearchSchema creation."""
        schema = SearchSchema(
            scope=Scope.BEATMAPS
        )

        assert schema.scope == Scope.BEATMAPS

    def test_search_schema_with_sorting(self):
        """Test SearchSchema with sorting."""
        schema = SearchSchema(
            scope=Scope.BEATMAPS,
            sorting=SortingSchema(root=[])
        )

        assert schema.sorting is not None

    def test_search_schema_with_filters(self):
        """Test SearchSchema with filters."""
        schema = SearchSchema(
            scope=Scope.BEATMAPS,
            filters=FiltersSchema()
        )

        assert schema.filters is not None

    def test_search_schema_with_search_terms(self):
        """Test SearchSchema with search terms."""
        schema = SearchSchema(
            scope=Scope.BEATMAPS,
            search_terms=SearchTermsSchema()
        )

        assert schema.search_terms is not None

    def test_search_schema_extra_forbidden(self):
        """Test SearchSchema forbids extra fields."""
        with pytest.raises(Exception):
            SearchSchema(
                scope=Scope.BEATMAPS,
                extra_field="value"
            )

    def test_conditions_max_regex_length(self):
        """Test Conditions validates regex length."""
        long_pattern = "a" * 150

        with pytest.raises(Exception):
            Conditions(regex=long_pattern)

    def test_conditions_empty_regex(self):
        """Test Conditions rejects empty regex."""
        with pytest.raises(Exception):
            Conditions(regex="")

    def test_conditions_dangerous_regex(self):
        """Test Conditions rejects dangerous regex."""
        dangerous_pattern = "(a+)+b"

        with pytest.raises(Exception):
            Conditions(regex=dangerous_pattern)

    def test_conditions_valid_regex(self):
        """Test Conditions accepts valid regex."""
        pattern = "test.*pattern"

        conditions = Conditions(regex=pattern)

        assert conditions.regex == pattern

    def test_conditions_max_groups(self):
        """Test Conditions validates capture groups."""
        pattern = "((a)(b)(c)(d)(e)(f)(g)(h)(i)(j))"

        with pytest.raises(Exception):
            Conditions(regex=pattern)

    def test_field_weights_creation(self):
        """Test FieldWeights creation."""
        weights = FieldWeights()

        assert weights is not None

    def test_pattern_multipliers_creation(self):
        """Test PatternMultipliers creation."""
        multipliers = PatternMultipliers()

        assert multipliers is not None

    def test_search_terms_creation(self):
        """Test SearchTerms creation."""
        terms = SearchTermsSchema()

        assert terms is not None

    def test_conditions_values_for_validation(self):
        """Test conditions values for validation."""
        conditions = Conditions(
            eq=123,
            gt=100,
            in_=[1, 2, 3]
        )

        values = conditions.values_for_validation()

        assert 123 in values
        assert 100 in values

    def test_field_filters_items(self):
        """Test FieldFilters items method."""
        filters = FieldFilters(root={
            "id": Conditions(eq=123),
            "name": Conditions(eq="test")
        })

        items = filters.items()

        assert len(list(items)) == 2

    def test_sorting_schema_iteration(self):
        """Test SortingSchema iteration."""
        schema = SortingSchema(root=[
            SortingOption(field=MagicMock()),
            SortingOption(field=MagicMock())
        ])

        options = list(schema)

        assert len(options) == 2

    def test_field_filters_len(self):
        """Test FieldFilters __len__."""
        filters = FieldFilters(root={
            "id": Conditions(eq=123)
        })

        assert len(filters) == 1

    def test_search_terms_validate_against_scope(self):
        """Test SearchTerms validate against scope."""
        terms = SearchTermsSchema()

        # Should not raise
        terms.validate_against_scope(Scope.BEATMAPS)

    def test_conditions_is_null_exclusive(self):
        """Test Conditions is_null is exclusive."""
        with pytest.raises(Exception):
            Conditions(is_null=True, eq=123)

    def test_conditions_range_validation(self):
        """Test Conditions range validation."""
        with pytest.raises(Exception):
            Conditions(gt=200, lt=100)

    def test_conditions_range_lte_validation(self):
        """Test Conditions lte range validation."""
        with pytest.raises(Exception):
            Conditions(gte=200, lt=100)

    def test_conditions_in_contains_eq(self):
        """Test Conditions in contains eq."""
        with pytest.raises(Exception):
            Conditions(eq=10, in_=[1, 2, 3])

    def test_conditions_eq_not_in_not_in(self):
        """Test Conditions eq not in not_in."""
        with pytest.raises(Exception):
            Conditions(eq=2, not_in=[1, 2, 3])
