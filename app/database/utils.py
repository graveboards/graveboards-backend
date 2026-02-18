from typing import Any, Union, get_origin, get_args, Iterable
from typing import cast as typing_cast

from sqlalchemy.sql import any_, all_, cast
from sqlalchemy.sql.elements import ColumnClause, literal, BinaryExpression, BindParameter, CollectionAggregate, ColumnElement
from sqlalchemy.sql.functions import func
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.dialects.postgresql import ARRAY

from app.exceptions import TypeValidationError
from app.search.enums import FilterOperator

__all__ = [
    "extract_inner_types",
    "validate_type",
    "get_filter_condition"
]


def extract_inner_types(annotated_type: Any) -> type | tuple[type, ...]:
    """Extract concrete inner types from nested typing annotations.

    Unwraps Optional, Union, and generic containers to determine the underlying runtime
    type(s).

    Args:
        annotated_type:
            A typing-annotated type.

    Returns:
        A single type or tuple of possible types.
    """
    current = annotated_type

    while get_origin(current):
        origin = get_origin(current)
        args = get_args(current)

        if origin is Union:
            non_none_args = [arg for arg in args if arg is not type(None)]
            return non_none_args[0] if len(non_none_args) == 1 else tuple(non_none_args)
        else:
            current = args[0] if args else current

    return current


def validate_type(expected_type: Any, value: Any):
    """Recursively validate a value against a typing annotation.

    Supports:
        - Union / Optional
        - list / tuple
        - dict
        - Numeric widening (int accepted for float)

    Args:
        expected_type:
            Typing annotation to validate against.
        value:
            Runtime value to validate.

    Raises:
        TypeValidationError:
            If validation fails at any level.
    """
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is Union:
        for arg in args:
            try:
                validate_type(arg, value)
                return
            except TypeValidationError:
                continue

        raise TypeValidationError(type(value), *args)

    if origin in (list, tuple):
        if not isinstance(value, origin):
            raise TypeValidationError(type(value), origin)

        iterable_value = typing_cast(Iterable[Any], value)
        item_types = args if origin is tuple and len(args) > 1 else [args[0]]

        for i, item in enumerate(iterable_value):
            expected_item_type = item_types[min(i, len(item_types) - 1)]
            validate_type(expected_item_type, item)

        return

    if origin is dict:
        if not isinstance(value, dict):
            raise TypeValidationError(type(value), dict)

        key_type, val_type = args

        for k, v in value.items():
            validate_type(key_type, k)
            validate_type(val_type, v)

        return

    if expected_type is float:
        if not isinstance(value, (float, int)):
            raise TypeValidationError(type(value), float, int)

        return

    if not isinstance(value, expected_type):
        raise TypeValidationError(type(value), expected_type)


def get_filter_condition(
    filter_operator: FilterOperator,
    target: InstrumentedAttribute | ColumnClause,
    value: Any,
    is_aggregated: bool = False
) -> BinaryExpression | BindParameter | CollectionAggregate | ColumnElement[bool]:
    """Construct a SQLAlchemy filter condition dynamically.

    For non-aggregated columns, delegates directly to the operator's bound method.

    For aggregated queries, constructs array-based comparisons using PostgreSQL
    aggregation functions to support filtering across grouped results.

    Args:
        filter_operator:
            Logical operator abstraction.
        target:
            Column or instrumented attribute being filtered.
        value:
            Comparison value.
        is_aggregated:
            Whether the filter applies to grouped results.

    Returns:
        SQLAlchemy boolean expression suitable for WHERE or HAVING.

    Raises:
        ValueError:
            If an unsupported filter operator is provided.
    """
    if not is_aggregated:
        return filter_operator.method(target, value)

    array_agg = func.array_agg(target)

    match filter_operator:
        case FilterOperator.EQ:
            return literal(value) == any_(array_agg)
        case FilterOperator.NEQ:
            return literal(value) != all_(array_agg)
        case FilterOperator.GT:
            return any_(array_agg) > literal(value)
        case FilterOperator.LT:
            return any_(array_agg) < literal(value)
        case FilterOperator.GTE:
            return any_(array_agg) >= literal(value)
        case FilterOperator.LTE:
            return any_(array_agg) <= literal(value)
        case FilterOperator.IN:
            return array_agg.op("&&")(cast(literal(value), ARRAY(target.type)))
        case FilterOperator.NOT_IN:
            return ~array_agg.op("&&")(cast(literal(value), ARRAY(target.type)))
        case FilterOperator.IS_NULL:
            return func.bool_and(target.is_(None))
        case FilterOperator.REGEX:
            return func.bool_or(target.op("~")(literal(value)))
        case FilterOperator.NOT_REGEX:
            return func.bool_and(~target.op("~")(literal(value)))
        case _:
            raise ValueError(f"Invalid filter operator: {filter_operator}")
