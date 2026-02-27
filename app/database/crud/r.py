from typing import Iterable, Any, Optional, Union

from sqlalchemy.sql import select, cast
from sqlalchemy.sql.sqltypes import String, Text
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement, and_
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.functions import func
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy.orm.relationships import RelationshipProperty, Relationship
from sqlalchemy.orm.strategy_options import selectinload, joinedload, noload, Load
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseType, ModelClass, Base
from app.database.utils import get_filter_condition, extract_inner_types
from app.database.enums import FilterOperator
from app.utils import clamp
from .decorators import session_manager
from .types import Sorting, Filters, Include

QUERY_MIN_LIMIT = 1
QUERY_MAX_LIMIT = 100
QUERY_DEFAULT_LIMIT = 50


class _R:
    @staticmethod
    async def _get_instance(
        model_class: ModelClass,
        session: AsyncSession,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _sorting: Sorting = None,
        _filters: Filters = None,
        _search: str = None,
        _include: Include = None,
        _offset: int = 0,
        **kwargs
    ) -> BaseType:
        """Fetch a single instance using a dynamically constructed query.

        This method composes a SQLAlchemy ``Select`` statement via ``_construct_stmt``,
        optionally applies an offset, and returns the first scalar result.

        Args:
            model_class:
                Wrapped model metadata used for validation and query construction.
            session:
                Active async SQLAlchemy session.
            _select:
                Column name(s) to project. If omitted, selects the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
            _filters:
                Nested filter configuration as a dict of fields and conditions.
            _search:
                Search query string.
            _include:
                Nested relationship loading configuration.
            _offset:
                Number of rows to skip before returning the first result.
            **kwargs:
                Additional equality filters applied via `filter_by()`.

        Returns:
            The first matching model instance or projected scalar value, or ``None`` if
            no result is found.
        """
        select_stmt = _R._construct_stmt(model_class, _select, _join, _where, _sorting, _filters, _include, **kwargs)
        select_stmt = select_stmt.offset(_offset)

        return await session.scalar(select_stmt)

    @staticmethod
    async def _get_instances(
        model_class: ModelClass,
        session: AsyncSession,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _sorting: Sorting = None,
        _filters: Filters = None,
        _search: str = None,
        _include: Include = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        **kwargs
    ) -> list[BaseType]:
        """Fetch multiple instances using a dynamically constructed query.

        Applies limit and offset constraints with bounds clamping, executes the query,
        and optionally reverses the result list in memory.

        Args:
            model_class:
                Wrapped model metadata used for validation and query construction.
            session:
                Active async SQLAlchemy session.
            _select:
                Column name(s) to project. If omitted, selects the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
            _filters:
                Nested filter configuration as a dict of fields and conditions.
            _search:
                Search query string.
            _include:
                Nested relationship loading configuration.
            _limit:
                Maximum number of rows to return. Clamped between configured bounds.
            _offset:
                Number of rows to skip before returning results.
            _reversed:
                If True, reverses the result list after retrieval.
            **kwargs:
                Additional equality filters applied via `filter_by()`.

        Returns:
            A list of matching model instances or projected scalar values.
        """
        select_stmt = _R._construct_stmt(model_class, _select, _join, _where, _sorting, _filters, _search, _include, **kwargs)
        select_stmt = select_stmt.limit(clamp(_limit, QUERY_MIN_LIMIT, QUERY_MAX_LIMIT)).offset(_offset)

        results = list((await session.scalars(select_stmt)).all())

        if _reversed:
            results.reverse()

        return results

    @staticmethod
    def _construct_stmt(
        model_class: ModelClass,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _sorting: Union[Any, Iterable[Any]] = None,
        _filters: Filters = None,
        _search: str = None,
        _include: Include = None,
        **kwargs
    ) -> Select:
        """Construct a SQLAlchemy ``Select`` statement from query parameters.

        This method orchestrates projection, joins, sorting, filtering, relationship
        loading, and lazy-exclusion rules into a single ``Select`` object.

        Args:
            model_class:
                Wrapped model metadata for validation and attribute access.
            _select:
                Column name(s) to project. If omitted, selects the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
            _filters:
                Nested filter configuration as a dict of fields and conditions.
            _search:
                Search query string.
            _include:
                Nested relationship loading configuration.
            **kwargs:
                Equality-based filters applied via `filter_by()`.

        Returns:
            A fully constructed SQLAlchemy ``Select`` statement.
        """
        if _select:
            select_stmt = _R._apply_select(model_class, _select)
        else:
            select_stmt = select(model_class.value)

        if _join is not None:
            select_stmt = _R._apply_join(select_stmt, _join)

        if _where:
            select_stmt = _R._apply_where(select_stmt, _where)

        if _sorting is not None:
            select_stmt = _R._apply_sorting(select_stmt, model_class, _sorting)
        else:
            select_stmt = select_stmt.order_by(*model_class.primary_keys)

        if _filters is not None:
            select_stmt = _R._apply_filters(select_stmt, model_class, _filters)

        if _search:
            select_stmt = _R._apply_search(select_stmt, model_class, _search)

        if _include and not _select:
            select_stmt = _R._apply_include(select_stmt, model_class, _include)

        if not _select:
            select_stmt = _R._apply_exclude_lazy(select_stmt, model_class, _include)

        select_stmt = select_stmt.filter_by(**kwargs)

        return select_stmt

    @staticmethod
    def _apply_select(
        model_class: ModelClass,
        select_: Union[str, Iterable[str]]
    ) -> Select:
        """Apply projection to a ``Select`` statement.

        Validates requested attribute names against the model metadata and restricts
        selection to columns or hybrid properties. Relationships cannot be projected
        directly.

        Args:
            model_class:
                Wrapped model metadata.
            select_:
                Column name or iterable of column names.

        Returns:
            A ``Select`` statement projecting only the requested attributes.

        Raises:
            ValueError:
                If an attribute does not exist or is a relationship.
        """
        if not isinstance(select_, (list, tuple, set)):
            select_ = [select_]

        model = model_class.value
        targets = []

        for name in select_:
            if name not in model_class.all_names:
                raise ValueError(f"Attribute '{name}' is not a valid column, relationship, nor hybrid property of {model_class.value}")

            if name in model_class.relationship_names:
                raise ValueError(f"Invalid attribute '{name}': cannot select relationships")

            targets.append(getattr(model, name))

        stmt = select(*targets)

        return stmt

    @staticmethod
    def _apply_join(
        select_stmt: Select,
        join: Union[type[BaseType], tuple[type[BaseType], BinaryExpression], Iterable[type[BaseType]], Iterable[tuple[type[BaseType], BinaryExpression]]]
    ) -> Select:
        """Apply one or more JOIN clauses to a ``Select`` statement.

        Accepts model classes or (model, condition) tuples. Input is normalized into an
        iterable of join targets before being applied sequentially.

        Args:
            select_stmt:
                The base ``Select`` statement.
            join:
                Join specification(s).

        Returns:
            The ``Select`` statement with joins applied.

        Raises:
            TypeError:
                If the join specification is invalid.
        """
        def is_base(t: Any) -> bool:
            return isinstance(t, type) and issubclass(t, Base)

        def is_tuple(t: Any) -> bool:
            return isinstance(t, tuple) and len(t) == 2 and issubclass(t[0], Base) and isinstance(t[1], BinaryExpression)

        if is_base(join):
            join = [(join,)]
        elif is_tuple(join):
            join = [join]
        elif isinstance(join, (list, tuple, set)):
            for i, target in enumerate(join):
                if is_base(target):
                    join[i] = [(target,)]
                elif is_tuple(target):
                    pass
                else:
                    raise TypeError(f"Invalid input for join: index={i}, value={target}")
        else:
            raise TypeError(f"Invalid input for join: {join}")

        for target in join:
            select_stmt = select_stmt.join(*target)

        return select_stmt

    @staticmethod
    def _apply_where(
        select_stmt: Select,
        where: Union[Any, Iterable[Any]]
    ) -> Select:
        """Apply WHERE clause expressions to a ``Select`` statement.

        Args:
            select_stmt:
                The base ``Select`` statement.
            where:
                A SQLAlchemy expression or iterable of expressions.

        Returns:
            The ``Select`` statement with WHERE conditions applied.
        """
        if not isinstance(where, (list, tuple, set)):
            where = [where]

        return select_stmt.where(*where)

    @staticmethod
    def _apply_sorting(
        select_stmt: Select,
        model_class: ModelClass,
        sorting: Sorting
    ) -> Select:
        """Apply validated sorting clauses to a ``Select`` statement.

        Only model columns and hybrid properties are sortable.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata for validation.
            sorting:
                List of dictionaries describing sorting rules.

        Returns:
            The ``Select`` statement with ORDER BY clauses applied.

        Raises:
            TypeError:
                If sorting is not a list of dicts.
            ValueError:
                If fields or ordering values are invalid.
        """
        if not isinstance(sorting, (list, tuple)):
            raise TypeError("_sorting must be a list of sorting objects")

        model = model_class.value
        model_name = model.__name__
        valid_fields = model_class.column_names | model_class.hybrid_property_names
        clauses = []

        for i, item in enumerate(sorting):
            if not isinstance(item, dict):
                raise TypeError(f"Invalid sorting item at index {i}: {item!r}")

            field = item.get("field")
            order = item.get("order", "asc")

            if not field:
                raise ValueError(f"Sorting item #{i} missing required 'field'")

            try:
                prefix, attr_name = field.split(".", 1)
            except ValueError:
                raise ValueError(f"Invalid field format '{field}' in item #{i}. Expected 'Model.field'")

            if prefix != model_name:
                raise ValueError(f"Sorting field '{field}' in item #{i} does not match model '{model_name}'")

            if attr_name not in valid_fields:
                raise ValueError(f"Attribute '{attr_name}' in item #{i} is not a valid column or hybrid property of {model_name}")

            attr = getattr(model, attr_name)

            if order not in ("asc", "desc"):
                raise ValueError(f"Invalid sorting order '{order}' in item #{i}. Must be 'asc' or 'desc'")

            clauses.append(attr.desc() if order == "desc" else attr.asc())

        return select_stmt.order_by(*clauses)

    @staticmethod
    def _apply_filters(
        select_stmt: Select,
        model_class: ModelClass,
        filters: Filters,
    ) -> Select:
        """Apply validated filter clauses to a ``Select`` statement.

        Supports both column-level conditions and nested relationship filtering.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata.
            filters:
                Dictionary describing filtering conditions.

        Returns:
            The ``Select`` statement with WHERE clauses applied.

        Raises:
            TypeError:
                If filtering structure is invalid.
            ValueError:
                If unsupported operators or attributes are encountered.
        """
        def parse_filters(
            parent_model_class: ModelClass,
            filters_: Filters,
            prefix: str = "",
        ) -> list[ColumnElement[bool]]:
            conditions: list[ColumnElement[bool]] = []

            for attr_name, value in filters_.items():
                path = f"{prefix}.{attr_name}" if prefix else attr_name
                is_attribute = attr_name in parent_model_class.column_names | parent_model_class.hybrid_property_names
                is_relationship = attr_name in parent_model_class.relationship_names

                if is_attribute:
                    column = getattr(parent_model_class.value, attr_name)

                    if not isinstance(value, dict):
                        operator = FilterOperator.EQ
                        conditions.append(get_filter_condition(operator, column, value))
                        continue

                    for op_name, op_value in value.items():
                        operator = FilterOperator.from_name(op_name)
                        conditions.append(get_filter_condition(operator, column, op_value))
                elif is_relationship:
                    if not isinstance(value, dict):
                        raise TypeError(f"Nested filter for relationship '{path}' must be a dict")

                    rel = parent_model_class.mapper.relationships[attr_name]
                    target_model_class = ModelClass(rel.mapper.class_)
                    relationship_attr = getattr(parent_model_class.value, attr_name)

                    nested_conditions = parse_filters(
                        target_model_class,
                        value,
                        path,
                    )

                    if not nested_conditions:
                        continue

                    if rel.uselist:
                        conditions.append(relationship_attr.any(and_(*nested_conditions)))
                    else:
                        conditions.append(relationship_attr.has(and_(*nested_conditions)))
                else:
                    raise ValueError(f"Attribute '{attr_name}' is not a valid field or relationship of {parent_model_class.value.__name__}")

            return conditions

        where_clauses = parse_filters(model_class, filters)

        if where_clauses:
            select_stmt = select_stmt.where(and_(*where_clauses))

        return select_stmt

    @staticmethod
    def _apply_search(
        select_stmt: Select,
        model_class: ModelClass,
        search: str,
    ) -> Select:
        """Apply full-text search to a ``Select`` statement.

        Search applies to all string columns and hybrid properties of the root model.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata.
            search:
                String with search terms.

        Returns:
            The ``Select`` statement with WHERE clauses applied.
        """
        model = model_class.value

        if not (search := search.strip()):
            return select_stmt

        string_columns = []

        for column_name in model_class.column_names:
            attr = getattr(model, column_name)

            try:
                if isinstance(attr.type, String):
                    string_columns.append(attr)
            except AttributeError:
                continue

        for hybrid_name in model_class.hybrid_property_names:
            column = model_class.value.__annotations__[hybrid_name]
            expected_type = extract_inner_types(column)

            if expected_type is str:
                attr = getattr(model, hybrid_name)
                string_columns.append(attr)

        if not string_columns:
            return select_stmt

        concatenated = func.concat_ws(
            " ",
            *[func.coalesce(cast(col, Text), "") for col in string_columns]
        )

        tsvector = func.to_tsvector("simple", concatenated)
        tsquery = func.websearch_to_tsquery("simple", search)
        search_condition = tsvector.op("@@")(tsquery)
        return select_stmt.where(search_condition)

    @staticmethod
    def _apply_include(
        select_stmt: Select,
        model_class: ModelClass,
        include: Include
    ) -> Select:
        """Apply eager-loading options based on a nested include specification.

        Supports nested relationship loading using `joinedload` or `selectinload`,
        depending on relationship cardinality. Boolean values control whether a
        relationship is loaded or suppressed.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata.
            include:
                Dictionary describing relationships to include.

        Returns:
            The ``Select`` statement with loader options applied.
        """

        def parse_node(
            attr: QueryableAttribute,
            rel_info: RelationshipProperty,
            target_model_class: ModelClass,
            value: Union[bool, Include],
            path: str
        ) -> LoaderOption:

            if isinstance(value, bool) and value:
                return selectinload(attr) if rel_info.uselist else joinedload(attr)
            elif isinstance(value, bool) and not value:
                return noload(attr)
            elif isinstance(value, dict):
                options = parse_includes(target_model_class, value, path)
                loader = selectinload(attr) if rel_info.uselist else joinedload(attr)
                return loader.options(*options)
            else:
                raise TypeError(f"Invalid value type for nested include '{attr.key}': Expected bool or dict, got {type(value).__name__}")

        def parse_includes(
            parent_model_class: ModelClass,
            includes: Include,
            prefix: str = ""
        ) -> list[LoaderOption]:
            options: list[LoaderOption] = []

            for attr_name, value in includes.items():
                if attr_name in parent_model_class.relationship_names:
                    attr = parent_model_class.mapper.attrs[attr_name]
                    rel_info = parent_model_class.mapper.relationships[attr_name]
                    target_model_class = ModelClass(rel_info.mapper.class_)
                    path = f"{prefix}.{attr_name}" if prefix else attr_name
                elif attr_name in parent_model_class.column_names | parent_model_class.hybrid_property_names:
                    continue  # Ignore columns and hybrid properties
                else:
                    raise ValueError(f"Attribute '{attr_name}' is not a valid relationship, column, nor property of {parent_model_class.value}")

                loader = parse_node(attr, rel_info, target_model_class, value, path)
                options.append(loader)

            return options

        load_options = parse_includes(model_class, include)
        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_exclude_lazy(
        select_stmt: Select,
        model_class: ModelClass,
        include: Include | None
    ) -> Select:
        """Prevent unintended lazy-loading of relationships.

        Any relationship not explicitly included is configured with `noload` to avoid
        implicit SELECT queries during attribute access. This enforces explicit loading
        behavior and guards against N+1 query issues.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata.
            include:
                Nested include specification.

        Returns:
            The ``Select`` statement with lazy exclusions applied.
        """
        if include is None:
            include = {}

        def is_lazy(rel: Relationship) -> bool:
            return rel.lazy in {True, "select", "dynamic"}

        def exclude_unincluded(
            parent_model_class,
            includes: Include,
            base_loader: Load = None
        ):
            options: list[LoaderOption] = []

            for rel in parent_model_class.mapper.relationships:
                if not is_lazy(rel):
                    continue

                attr = parent_model_class.mapper.attrs[rel.key]

                loader = (
                    base_loader.noload(attr)
                    if base_loader is not None
                    else noload(attr)
                )

                if rel.key not in includes:
                    options.append(loader)
                    continue

                value = includes[rel.key]

                if value is False or (isinstance(value, dict) and not value):
                    options.append(loader)
                    continue

                if value is True:
                    value = {}  # No sub-relationships of attr are loaded

                next_base = (
                    base_loader.selectinload(attr)
                    if rel.uselist
                    else base_loader.joinedload(attr)
                ) if base_loader else (
                    selectinload(attr)
                    if rel.uselist
                    else joinedload(attr)
                )

                target_model_class = ModelClass(rel.mapper.class_)
                options.extend(
                    exclude_unincluded(
                        target_model_class,
                        value,
                        next_base
                    )
                )

            return options

        load_options = exclude_unincluded(model_class, include)
        return select_stmt.options(*load_options)


class R(_R):
    @session_manager()
    async def get(
        self,
        model: type[BaseType],
        session: AsyncSession = None,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _sorting: Sorting = None,
        _filters: Filters = None,
        _search: str = None,
        _include: Include = None,
        _offset: int = 0,
        **kwargs
    ) -> Optional[BaseType]:
        """Public API for fetching a single model instance.

        Wraps ``_get_instance`` and manages session lifecycle via the
        ``session_manager`` decorator.

        Args:
            model:
                SQLAlchemy model class.
            session:
                Optional externally managed async session.
            _select:
                Column name or iterable of column names to project. If omitted, selects
                the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
            _filters:
                Nested filter configuration as a dict of fields and conditions.
            _search:
                Search query string.
            _include:
                Nested relationship loading specification.
            _offset:
                Number of rows to skip before returning the first result.
            **kwargs:
                Additional equality filters applied via `filter_by()`.

        Returns:
            The first matching model instance or projected scalar value, or ``None`` if
            no result is found.
        """
        model_class = ModelClass(model)

        return await self._get_instance(
            model_class,
            session,
            _select=_select,
            _join=_join,
            _where=_where,
            _sorting=_sorting,
            _filters=_filters,
            _search=_search,
            _include=_include,
            _offset=_offset,
            **kwargs
        )

    @session_manager()
    async def get_many(
        self,
        model: type[BaseType],
        session: AsyncSession = None,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _sorting: Sorting = None,
        _filters: Filters = None,
        _search: str = None,
        _include: Include = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        **kwargs
    ) -> list[BaseType]:
        """Public API for fetching multiple model instances.

        Wraps ``_get_instances`` and manages session lifecycle via the
        ``session_manager`` decorator.

        Args:
            model:
                SQLAlchemy model class.
            session:
                Optional externally managed async session.
            _select:
                Column name or iterable of column names to project. If omitted, selects
                the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
            _filters:
                Nested filter configuration as a dict of fields and conditions.
            _search:
                Search query string.
            _include:
                Nested relationship loading specification.
            _limit:
                Maximum number of rows to return. Clamped between configured bounds.
            _offset:
                Number of rows to skip before returning results.
            _reversed:
                If True, reverses the result list after retrieval.
            **kwargs:
                Additional equality filters applied via `filter_by()`.

        Returns:
            A list of matching model instances or projected scalar values.
        """
        model_class = ModelClass(model)

        return await self._get_instances(
            model_class,
            session,
            _select=_select,
            _join=_join,
            _where=_where,
            _sorting=_sorting,
            _filters=_filters,
            _search=_search,
            _include=_include,
            _limit=_limit,
            _offset=_offset,
            _reversed=_reversed,
            **kwargs
        )
