import pytest
from sqlalchemy import column

from app.database.utils import (
    extract_inner_types,
    validate_type,
    get_filter_condition
)
from app.exceptions import TypeValidationError
from app.database.enums import FilterOperator


class TestExtractInnerTypes:
    def test_unwraps_optional_type(self):
        from typing import Optional

        result = extract_inner_types(Optional[int])
        assert result is int

    def test_unwraps_union_type(self):
        from typing import Union

        result = extract_inner_types(Union[int, str])
        assert result is int

    def test_unwraps_list_type(self):
        from typing import List

        result = extract_inner_types(List[int])
        assert result is int

    def test_unwraps_tuple_type(self):
        from typing import Tuple

        result = extract_inner_types(Tuple[int, str])
        assert result is int

    def test_unwraps_nested_optional(self):
        from typing import Optional, List

        result = extract_inner_types(Optional[List[int]])
        assert result is List[int]

    def test_returns_plain_type_unmodified(self):
        result = extract_inner_types(int)
        assert result is int

    def test_returns_tuple_when_multiple_union_types(self):
        from typing import Union

        result = extract_inner_types(Union[int, str, float])
        assert result == (int, str, float)


class TestValidateType:
    def test_validates_int(self):
        validate_type(int, 42)

    def test_validates_float(self):
        validate_type(float, 3.14)

    def test_validates_int_as_float(self):
        validate_type(float, 42)

    def test_validates_string(self):
        validate_type(str, "hello")

    def test_validates_bool(self):
        validate_type(bool, True)

    def test_validates_list_of_ints(self):
        from typing import List
        validate_type(List[int], [1, 2, 3])

    def test_validates_list_of_strings(self):
        from typing import List
        validate_type(List[str], ["a", "b", "c"])

    def test_validates_tuple(self):
        from typing import Tuple
        validate_type(Tuple[int, str], (42, "hello"))

    def test_validates_dict(self):
        from typing import Dict
        validate_type(Dict[str, int], {"a": 1, "b": 2})

    def test_validates_nested_list(self):
        from typing import List
        validate_type(List[List[int]], [[1, 2], [3, 4]])

    def test_validates_nested_dict(self):
        from typing import Dict
        validate_type(Dict[str, Dict[str, int]], {"a": {"b": 1}})

    def test_rejects_string_for_int(self):
        with pytest.raises(TypeValidationError):
            validate_type(int, "string")

    def test_rejects_float_for_int(self):
        with pytest.raises(TypeValidationError):
            validate_type(int, 3.14)

    def test_rejects_int_for_string(self):
        with pytest.raises(TypeValidationError):
            validate_type(str, 42)

    def test_rejects_wrong_list_element_type(self):
        from typing import List
        with pytest.raises(TypeValidationError):
            validate_type(List[int], [1, "string", 3])

    def test_rejects_wrong_dict_key_type(self):
        from typing import Dict
        with pytest.raises(TypeValidationError):
            validate_type(Dict[int, str], {1: "a", "b": 2})

    def test_rejects_wrong_dict_value_type(self):
        from typing import Dict
        with pytest.raises(TypeValidationError):
            validate_type(Dict[str, int], {"a": "string"})

    def test_validates_union_type_int(self):
        from typing import Union
        validate_type(Union[int, str], 42)

    def test_validates_union_type_str(self):
        from typing import Union
        validate_type(Union[int, str], "hello")

    def test_validates_optional_int(self):
        from typing import Optional
        validate_type(Optional[int], 42)

    def test_validates_optional_none(self):
        from typing import Optional
        validate_type(Optional[int], None)

    def test_rejects_unsupported_type_in_union(self):
        from typing import Union
        with pytest.raises(TypeValidationError):
            validate_type(Union[int, str], 3.14)


class TestGetFilterCondition:
    def test_eq_operator_on_column(self, db_session):
        from app.database.models import User

        condition = get_filter_condition(
            FilterOperator.EQ,
            User.id,
            123
        )

        assert condition is not None

    def test_eq_operator_on_clause(self, db_session):
        condition = get_filter_condition(
            FilterOperator.EQ,
            column("test_column"),
            123
        )

        assert condition is not None

    def test_neq_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.NEQ,
            column("test_column"),
            123
        )

        assert condition is not None

    def test_gt_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.GT,
            column("test_column"),
            100
        )

        assert condition is not None

    def test_lt_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.LT,
            column("test_column"),
            100
        )

        assert condition is not None

    def test_gte_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.GTE,
            column("test_column"),
            100
        )

        assert condition is not None

    def test_lte_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.LTE,
            column("test_column"),
            100
        )

        assert condition is not None

    def test_in_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.IN,
            column("test_column"),
            [1, 2, 3]
        )

        assert condition is not None

    def test_not_in_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.NOT_IN,
            column("test_column"),
            [1, 2, 3]
        )

        assert condition is not None

    def test_is_null_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.IS_NULL,
            column("test_column"),
            None
        )

        assert condition is not None

    def test_regex_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.REGEX,
            column("test_column"),
            "pattern"
        )

        assert condition is not None

    def test_not_regex_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.NOT_REGEX,
            column("test_column"),
            "pattern"
        )

        assert condition is not None

    def test_invalid_operator_raises_value_error(self, db_session):

        with pytest.raises(ValueError):
            class FakeOperator:
                pass

            fake_op = FakeOperator()
            fake_op.method = lambda x, y: None
            get_filter_condition(fake_op, column("test"), 1)

    def test_aggregated_eq_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.EQ,
            column("test_column"),
            123,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_neq_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.NEQ,
            column("test_column"),
            123,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_gt_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.GT,
            column("test_column"),
            100,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_lt_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.LT,
            column("test_column"),
            100,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_gte_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.GTE,
            column("test_column"),
            100,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_lte_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.LTE,
            column("test_column"),
            100,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_in_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.IN,
            column("test_column"),
            [1, 2, 3],
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_not_in_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.NOT_IN,
            column("test_column"),
            [1, 2, 3],
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_is_null_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.IS_NULL,
            column("test_column"),
            None,
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_regex_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.REGEX,
            column("test_column"),
            "pattern",
            is_aggregated=True
        )

        assert condition is not None

    def test_aggregated_not_regex_operator(self, db_session):
        condition = get_filter_condition(
            FilterOperator.NOT_REGEX,
            column("test_column"),
            "pattern",
            is_aggregated=True
        )

        assert condition is not None
