from typing import Any, cast

import pytest
from sqlalchemy import column

from app.database.enums import FilterOperator
from app.database.utils import extract_inner_types, get_filter_condition, validate_type
from app.exceptions import TypeValidationError


class TestExtractInnerTypes:
    def test_unwraps_optional_type(self) -> None:
        result = extract_inner_types(int | None)
        assert result is int

    def test_unwraps_union_type(self) -> None:
        result = extract_inner_types(int | str)
        assert result is int

    def test_unwraps_list_type(self) -> None:

        result = extract_inner_types(list[int])
        assert result is int

    def test_unwraps_tuple_type(self) -> None:

        result = extract_inner_types(tuple[int, str])
        assert result is int

    def test_unwraps_nested_optional(self) -> None:
        result = extract_inner_types(list[int] | None)
        assert result == list[int]

    def test_returns_plain_type_unmodified(self) -> None:
        result = extract_inner_types(int)
        assert result is int

    def test_returns_tuple_when_multiple_union_types(self) -> None:
        result = extract_inner_types(int | str | float)
        assert result == (int, str, float)


class TestValidateType:
    def test_validates_int(self) -> None:
        validate_type(int, 42)

    def test_validates_float(self) -> None:
        validate_type(float, 3.14)

    def test_validates_int_as_float(self) -> None:
        validate_type(float, 42)

    def test_validates_string(self) -> None:
        validate_type(str, "hello")

    def test_validates_bool(self) -> None:
        validate_type(bool, True)

    def test_validates_list_of_ints(self) -> None:
        validate_type(list[int], [1, 2, 3])

    def test_validates_list_of_strings(self) -> None:
        validate_type(list[str], ["a", "b", "c"])

    def test_validates_tuple(self) -> None:
        validate_type(tuple[int, str], (42, "hello"))

    def test_validates_dict(self) -> None:
        validate_type(dict[str, int], {"a": 1, "b": 2})

    def test_validates_nested_list(self) -> None:
        validate_type(list[list[int]], [[1, 2], [3, 4]])

    def test_validates_nested_dict(self) -> None:
        validate_type(dict[str, dict[str, int]], {"a": {"b": 1}})

    def test_rejects_string_for_int(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(int, "string")

    def test_rejects_float_for_int(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(int, 3.14)

    def test_rejects_int_for_string(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(str, 42)

    def test_rejects_wrong_list_element_type(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(list[int], [1, "string", 3])

    def test_rejects_wrong_dict_key_type(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(dict[int, str], {1: "a", "b": 2})

    def test_rejects_wrong_dict_value_type(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(dict[str, int], {"a": "string"})

    def test_validates_union_type_int(self) -> None:
        validate_type(int | str, 42)

    def test_validates_union_type_str(self) -> None:
        validate_type(int | str, "hello")

    def test_validates_optional_int(self) -> None:
        validate_type(int | None, 42)

    def test_validates_optional_none(self) -> None:
        validate_type(int | None, None)

    def test_rejects_unsupported_type_in_union(self) -> None:
        with pytest.raises(TypeValidationError):
            validate_type(int | str, 3.14)


class TestGetFilterCondition:
    def test_eq_operator_on_column(self, db_session: Any) -> None:
        from app.database.models import User

        condition = get_filter_condition(FilterOperator.EQ, User.id, 123)

        assert condition is not None

    def test_eq_operator_on_clause(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.EQ, column("test_column"), 123)

        assert condition is not None

    def test_neq_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.NEQ, column("test_column"), 123)

        assert condition is not None

    def test_gt_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.GT, column("test_column"), 100)

        assert condition is not None

    def test_lt_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.LT, column("test_column"), 100)

        assert condition is not None

    def test_gte_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.GTE, column("test_column"), 100)

        assert condition is not None

    def test_lte_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.LTE, column("test_column"), 100)

        assert condition is not None

    def test_in_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.IN, column("test_column"), [1, 2, 3])

        assert condition is not None

    def test_not_in_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.NOT_IN, column("test_column"), [1, 2, 3])

        assert condition is not None

    def test_is_null_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.IS_NULL, column("test_column"), None)

        assert condition is not None

    def test_regex_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.REGEX, column("test_column"), "pattern")

        assert condition is not None

    def test_not_regex_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(FilterOperator.NOT_REGEX, column("test_column"), "pattern")

        assert condition is not None

    def test_invalid_operator_raises_value_error(self, db_session: Any) -> None:

        class FakeOperator:
            def method(self, x: int, y: int) -> None:
                return None

        fake_op = FakeOperator()
        with pytest.raises(ValueError):
            get_filter_condition(cast("FilterOperator", fake_op), column("test"), 1)

    def test_aggregated_eq_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.EQ, column("test_column"), 123, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_neq_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.NEQ, column("test_column"), 123, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_gt_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.GT, column("test_column"), 100, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_lt_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.LT, column("test_column"), 100, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_gte_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.GTE, column("test_column"), 100, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_lte_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.LTE, column("test_column"), 100, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_in_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.IN, column("test_column"), [1, 2, 3], is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_not_in_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.NOT_IN, column("test_column"), [1, 2, 3], is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_is_null_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.IS_NULL, column("test_column"), None, is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_regex_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.REGEX, column("test_column"), "pattern", is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_not_regex_operator(self, db_session: Any) -> None:
        condition = get_filter_condition(
            FilterOperator.NOT_REGEX, column("test_column"), "pattern", is_aggregated=True
        )

        assert condition is not None
