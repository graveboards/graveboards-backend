import pytest

from app.database.utils import get_filter_condition
from app.database.enums import FilterOperator


class TestGetFilterCondition:
    def test_eq_operator_non_aggregated(self, mock_column_clause):
        condition = get_filter_condition(FilterOperator.EQ, mock_column_clause, 42)

        assert condition is not None

    def test_eq_operator_aggregated(self, mock_column_clause):
        condition = get_filter_condition(FilterOperator.EQ, mock_column_clause, 42, is_aggregated=True)

        assert condition is not None

    def test_in_operator_aggregated(self, mock_column_clause):
        condition = get_filter_condition(FilterOperator.IN, mock_column_clause, [1, 2, 3], is_aggregated=True)

        assert condition is not None

    def test_unsupported_operator_raises_value_error(self):
        with pytest.raises(ValueError):
            get_filter_condition("invalid_operator", None, 42)


@pytest.fixture
def mock_column_clause():
    from unittest.mock import MagicMock
    from sqlalchemy.sql.elements import ColumnClause

    column = MagicMock(spec=ColumnClause)
    return column
