from __future__ import annotations
from collections.abc import Iterable
from types import EllipsisType
from typing import Any, Literal, TypeGuard, overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm.strategy_options import Load, _AbstractLoad, joinedload, noload, selectinload
from sqlalchemy.sql import cast, select
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement, and_, or_
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.sqltypes import String, Text

from app.database.ctes.search_terms_filtered import search_terms_filtered_cte_factory
from app.database.ctes.search_terms_scored import search_terms_scored_ctes_factory
from app.database.enums import FilterOperator
from app.database.models import (
    Base,
    ModelClass,
)
from app.database.utils import extract_inner_types, get_filter_condition
from app.search.datastructures import SearchTermsSchema
from app.search.enums import Scope
from app.search.mappings import SCOPE_MODEL_MAPPING
from app.utils import clamp

from .decorators import require_session, session_manager
from .relevance import SCOPE_RELEVANCE_HANDLERS
from .types import Filters, Include, Sorting

QUERY_MIN_LIMIT = 1
QUERY_MAX_LIMIT = 100
QUERY_DEFAULT_LIMIT = 50
SearchMode = Literal["simple", "engine"]

type JoinTarget = type[Base] | tuple[type[Base], BinaryExpression]
type JoinTargets = JoinTarget | Iterable[JoinTarget]
type WhereClause = BinaryExpression | Iterable[BinaryExpression]

MODEL_SCOPE_MAPPING: dict[ModelClass[Any], Scope] = {
    model_class: scope
    for scope, model_class in SCOPE_MODEL_MAPPING.items()
    if not isinstance(model_class, EllipsisType)
}


class _R:
    @staticmethod
    async def _get_instance[M: Base](
        model_class: ModelClass[M], session: AsyncSession, /,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _offset: int = 0,
        **kwargs: Any,
    ) -> M | None:
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
            _search_mode:
                Search strategy ("simple" or "engine").
            _search_relevance:
                If ``True``, apply relevance ordering for engine searches.
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
        select_stmt = _R._construct_stmt(
            model_class,
            _select,
            _join,
            _where,
            _sorting,
            _filters,
            _search,
            _search_mode,
            _search_relevance,
            _include,
            **kwargs,
        )
        select_stmt = select_stmt.offset(_offset)

        result: M | None = await session.scalar(select_stmt)
        return result

    @overload
    @staticmethod
    async def _get_instances[M: Base](
        model_class: ModelClass[M], session: AsyncSession, /, *,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        _count: Literal[False] = False,
        **kwargs: Any,
    ) -> list[M]: ...

    @overload
    @staticmethod
    async def _get_instances[M: Base](
        model_class: ModelClass[M], session: AsyncSession, /, *,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        _count: Literal[True],
        **kwargs: Any,
    ) -> tuple[list[M], int | None]: ...

    @staticmethod
    async def _get_instances[M: Base](
        model_class: ModelClass[M], session: AsyncSession, /, *,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        _count: bool = False,
        **kwargs: Any,
    ) -> list[M] | tuple[list[M], int | None]:
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
            _search_mode:
                Search strategy ("simple" or "engine").
            _search_relevance:
                If ``True``, apply relevance ordering for engine searches.
            _include:
                Nested relationship loading configuration.
            _limit:
                Maximum number of rows to return. Clamped between configured bounds.
            _offset:
                Number of rows to skip before returning results.
            _reversed:
                If True, reverses the result list after retrieval.
            _count:
                If True, also returns the total count of matching rows (without limit/offset).
            **kwargs:
                Additional equality filters applied via `filter_by()`.

        Returns:
            A list of matching model instances or projected scalar values.
            If _count is True, returns a tuple of (results, total_count).
        """
        select_stmt = _R._construct_stmt(
            model_class,
            _select,
            _join,
            _where,
            _sorting,
            _filters,
            _search,
            _search_mode,
            _search_relevance,
            _include,
            **kwargs,
        )

        if _count:
            count_stmt = select(func.count()).select_from(select_stmt.subquery())
            total = await session.scalar(count_stmt)
            count_results: list[M] = list((await session.scalars(select_stmt)).all())
            return count_results, total

        select_stmt = select_stmt.limit(clamp(_limit, QUERY_MIN_LIMIT, QUERY_MAX_LIMIT)).offset(
            _offset
        )
        results: list[M] = list((await session.scalars(select_stmt)).all())

        if _reversed:
            results.reverse()

        return results

    @staticmethod
    def _construct_stmt(
        model_class: ModelClass[Any],
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        **kwargs: Any,
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
            _search_mode:
                Search strategy ("simple" or "engine").
            _search_relevance:
                If ``True``, apply relevance ordering for engine searches.
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

        joined_models: dict[str, type[Base]] = {}

        if _join is not None:
            select_stmt, joined_models = _R._apply_join(select_stmt, _join)

        if _where is not None:
            select_stmt = _R._apply_where(select_stmt, _where)

        if _sorting is not None:
            select_stmt = _R._apply_sorting(
                select_stmt, model_class, _sorting, joined_models=joined_models
            )
        else:
            select_stmt = select_stmt.order_by(*model_class.primary_keys)

        if _filters is not None:
            select_stmt = _R._apply_filters(select_stmt, model_class, _filters)

        select_stmt = select_stmt.filter_by(**kwargs)

        if _search:
            select_stmt = _R._apply_search(
                select_stmt,
                model_class,
                _search,
                mode=_search_mode,
                relevance=_search_relevance and _sorting is None,
            )

        if _include and not _select:
            select_stmt = _R._apply_include(select_stmt, model_class, _include)

        if not _select:
            select_stmt = _R._apply_exclude_lazy(select_stmt, model_class, _include)

        return select_stmt

    @staticmethod
    def _apply_select(model_class: ModelClass[Any], select_: str | Iterable[str]) -> Select:
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
            TypeError:
                If select_ is not a string or iterable of strings.
        """
        model = model_class.value
        targets = []

        def append_target(name_: str) -> None:
            if name_ not in model_class.all_names:
                raise ValueError(
                    f"Attribute '{name_}' is not a valid column, relationship, nor hybrid property of {model_class.value}"
                )

            if name_ in model_class.relationship_names:
                raise ValueError(f"Invalid attribute '{name_}': cannot select relationships")

            targets.append(getattr(model, name_))

        if isinstance(select_, (list, tuple, set)) and all(
            isinstance(name, str) for name in select_
        ):
            for name in select_:
                append_target(name)
        elif isinstance(select_, str):
            append_target(select_)
        else:
            raise TypeError(
                f"select_ must be string or iterable of strings, got {type(select_).__name__}"
            )

        stmt = select(*targets)
        return stmt

    @staticmethod
    def _apply_join(
        select_stmt: Select,
        join: JoinTargets,
    ) -> tuple[Select, dict[str, type[Base]]]:
        """Apply one or more JOIN clauses to a ``Select`` statement.

        Accepts model classes or (model, condition) tuples. Input is normalized into an
        iterable of join targets before being applied sequentially.

        Args:
            select_stmt:
                The base ``Select`` statement.
            join:
                Join specification(s).

        Returns:
            A tuple of the ``Select`` statement with joins applied, and a mapping of
            joined model names to their types.

        Raises:
            TypeError:
                If the join specification is invalid.
        """

        def is_base(t: Any) -> TypeGuard[type[Base]]:
            return isinstance(t, type) and issubclass(t, Base)

        def is_tuple(t: Any) -> TypeGuard[tuple[type[Base], BinaryExpression]]:
            return (
                isinstance(t, tuple)
                and len(t) == 2
                and issubclass(t[0], Base)
                and isinstance(t[1], BinaryExpression)
            )

        def normalize(
            t: Any, index: int | None = None
        ) -> tuple[type[Base], BinaryExpression | None]:
            if is_base(t):
                return t, None
            if is_tuple(t):
                return t[0], t[1]

            location = f"index={index}, " if index is not None else ""
            raise TypeError(f"Invalid input for join: {location}value={t}")

        join_targets: list[tuple[type[Base], BinaryExpression | None]]

        if is_base(join) or is_tuple(join):
            join_targets = [normalize(join)]
        elif isinstance(join, (list, tuple, set)):
            join_targets = [normalize(target, i) for i, target in enumerate(join)]
        else:
            raise TypeError(f"Invalid input for join: {join}")

        joined_models: dict[str, type[Base]] = {}

        for model, condition in join_targets:
            select_stmt = (
                select_stmt.join(model) if condition is None else select_stmt.join(model, condition)
            )
            joined_models[model.__name__] = model

        return select_stmt, joined_models

    @staticmethod
    def _apply_where(select_stmt: Select, where: WhereClause) -> Select:
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
            where = [where]  # type: ignore[list-item]

        return select_stmt.where(*where)

    @staticmethod
    def _apply_sorting(
        select_stmt: Select,
        model_class: ModelClass[Any],
        sorting: Sorting,
        joined_models: dict[str, type[Base]] | None = None,
    ) -> Select:
        """Apply validated sorting clauses to a ``Select`` statement.

        Only model columns and hybrid properties are sortable. Sorting by fields on
        joined models is also supported when ``joined_models`` is provided.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata for validation.
            sorting:
                List of dictionaries describing sorting rules.
            joined_models:
                Mapping of joined model names to their types, allowing sorting by
                their columns.

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
                raise ValueError(
                    f"Invalid field format '{field}' in item #{i}. Expected 'Model.field'"
                ) from None

            if prefix == model_name:
                target_model = model
                valid_target_fields = valid_fields
            elif joined_models is not None and prefix in joined_models:
                target_model = joined_models[prefix]
                target_model_class = ModelClass.from_model(target_model)
                valid_target_fields = (
                    target_model_class.column_names | target_model_class.hybrid_property_names
                )
            else:
                raise ValueError(
                    f"Sorting field '{field}' in item #{i} does not match model '{model_name}' or any joined model"
                )

            if attr_name not in valid_target_fields:
                raise ValueError(
                    f"Attribute '{attr_name}' in item #{i} is not a valid column or hybrid property of {prefix}"
                )

            attr = getattr(target_model, attr_name)

            if order not in ("asc", "desc"):
                raise ValueError(
                    f"Invalid sorting order '{order}' in item #{i}. Must be 'asc' or 'desc'"
                )

            clauses.append(attr.desc() if order == "desc" else attr.asc())

        return select_stmt.order_by(*clauses)

    @staticmethod
    def _apply_filters(
        select_stmt: Select,
        model_class: ModelClass[Any],
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
            parent_model_class: ModelClass[Any],
            filters_: Filters,
            prefix: str = "",
        ) -> list[ColumnElement[bool]]:
            conditions: list[ColumnElement[bool]] = []

            for attr_name, value in filters_.items():
                path = f"{prefix}.{attr_name}" if prefix else attr_name
                is_attribute = (
                    attr_name
                    in parent_model_class.column_names | parent_model_class.hybrid_property_names
                )
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
                    target_model_class = ModelClass.from_model(rel.mapper.class_)
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
                    raise ValueError(
                        f"Attribute '{attr_name}' is not a valid field or relationship of {parent_model_class.value.__name__}"
                    )

            return conditions

        where_clauses = parse_filters(model_class, filters)

        if where_clauses:
            select_stmt = select_stmt.where(and_(*where_clauses))

        return select_stmt

    @staticmethod
    def _apply_search(
        select_stmt: Select,
        model_class: ModelClass[Any],
        search: str,
        mode: SearchMode = "simple",
        relevance: bool = False,
    ) -> Select:
        """Apply search to a ``Select`` statement.

        Modes:
            - ``simple``: Search applies to all string columns and hybrid properties of the root model.
            - ``engine``: Search applies scope-aware relationship mappings via search-term CTEs.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata.
            search:
                String with search terms.
            mode:
                Search strategy ("simple" or "engine").
            relevance:
                If ``True``, apply relevance ordering for engine searches.
                This is ignored for simple search and when explicit sorting is applied.

        Returns:
            The ``Select`` statement with WHERE clauses applied.
        """
        if not (search := search.strip()):
            return select_stmt
        if mode == "engine":
            engine_stmt = _R._apply_search_engine(
                select_stmt, model_class, search, relevance=relevance
            )
            if engine_stmt is not None:
                return engine_stmt

        return _R._apply_search_simple(select_stmt, model_class, search)

    @staticmethod
    def _apply_search_engine(
        select_stmt: Select,
        model_class: ModelClass[Any],
        search: str,
        relevance: bool = False,
    ) -> Select | None:
        """Apply scope-aware search term filtering using the main search mappings."""
        scope: Scope | None = MODEL_SCOPE_MAPPING.get(model_class)

        if scope is None:
            return None

        search_terms = SearchTermsSchema.model_validate({"terms": search})
        filter_cte = search_terms_filtered_cte_factory(scope, search_terms)

        select_stmt = select_stmt.join(filter_cte, filter_cte.c.id == model_class.value.id)

        if not relevance:
            return select_stmt

        return _R._apply_search_engine_relevance(select_stmt, scope, search_terms)

    @staticmethod
    def _apply_search_engine_relevance(
        select_stmt: Select, scope: Scope, search_terms: SearchTermsSchema
    ) -> Select:
        """Apply relevance-based ordering for engine searches."""
        category_score_ctes = search_terms_scored_ctes_factory(scope, search_terms)
        handler = SCOPE_RELEVANCE_HANDLERS.get(scope)

        if handler is None:
            return select_stmt

        return handler(select_stmt, category_score_ctes, search_terms)  # type: ignore[arg-type]

    @staticmethod
    def _apply_search_simple(
        select_stmt: Select,
        model_class: ModelClass[Any],
        search: str,
    ) -> Select:
        """Apply full-text + substring search to a ``Select`` statement."""
        model = model_class.value

        string_columns = [
            getattr(model, name)
            for name in model_class.column_names
            if isinstance(getattr(model, name).type, String)
        ]

        string_columns += [
            getattr(model, name)
            for name in model_class.hybrid_property_names
            if extract_inner_types(model.__annotations__[name]) is str
        ]

        if not string_columns:
            return select_stmt

        concatenated = func.concat_ws(
            " ",
            *[func.coalesce(cast(col, Text), "") for col in string_columns],
        )

        fts_condition = func.to_tsvector("simple", concatenated).op("@@")(
            func.websearch_to_tsquery("simple", search)
        )

        terms = search.split()

        substring_condition = and_(
            *[
                or_(*[cast(col, Text).ilike(f"%{term}%") for col in string_columns])
                for term in terms
            ]
        )

        return select_stmt.where(or_(fts_condition, substring_condition))

    @staticmethod
    def _apply_include(select_stmt: Select, model_class: ModelClass[Any], include: Include) -> Select:
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
            target_model_class: ModelClass[Any],
            value: bool | Include,
            path: str,
        ) -> LoaderOption:

            if isinstance(value, bool) and value:
                return selectinload(attr) if rel_info.uselist else joinedload(attr)
            elif isinstance(value, bool) and not value:
                return noload(attr)
            elif isinstance(value, dict):
                options = parse_includes(target_model_class, value, path)
                loader = selectinload(attr) if rel_info.uselist else joinedload(attr)
                return loader.options(*options)  # type: ignore[arg-type]
            else:
                raise TypeError(
                    f"Invalid value type for nested include '{attr.key}': Expected bool or dict, got {type(value).__name__}"
                )

        def parse_includes(
            parent_model_class: ModelClass[Any], includes: Include, prefix: str = ""
        ) -> list[LoaderOption]:
            options: list[LoaderOption] = []

            for attr_name, value in includes.items():
                if attr_name in parent_model_class.relationship_names:
                    attr: QueryableAttribute[Any] = getattr(parent_model_class.value, attr_name)
                    rel_info = parent_model_class.mapper.relationships[attr_name]
                    target_model_class = ModelClass.from_model(rel_info.mapper.class_)
                    path = f"{prefix}.{attr_name}" if prefix else attr_name
                elif (
                    attr_name
                    in parent_model_class.column_names | parent_model_class.hybrid_property_names
                ):
                    continue  # Ignore columns and hybrid properties
                else:
                    raise ValueError(
                        f"Attribute '{attr_name}' is not a valid relationship, column, nor property of {parent_model_class.value}"
                    )

                loader = parse_node(attr, rel_info, target_model_class, value, path)
                options.append(loader)

            return options

        load_options = parse_includes(model_class, include)
        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_exclude_lazy(
        select_stmt: Select, model_class: ModelClass[Any], include: Include | None
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

        def is_lazy(rel: RelationshipProperty) -> bool:
            return rel.lazy in {True, "select", "dynamic"}

        def exclude_unincluded(
            parent_model_class: ModelClass[Any], includes: Include, base_loader: _AbstractLoad | None = None
        ) -> list[LoaderOption]:
            options: list[LoaderOption] = []

            for rel in parent_model_class.mapper.relationships:
                if not is_lazy(rel):
                    continue

                attr: QueryableAttribute[Any] = getattr(parent_model_class.value, rel.key)

                loader = base_loader.noload(attr) if base_loader is not None else noload(attr)

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
                    (
                        base_loader.selectinload(attr)
                        if rel.uselist
                        else base_loader.joinedload(attr)
                    )
                    if base_loader
                    else (selectinload(attr) if rel.uselist else joinedload(attr))
                )

                target_model_class = ModelClass.from_model(rel.mapper.class_)
                options.extend(exclude_unincluded(target_model_class, value, next_base))

            return options

        load_options = exclude_unincluded(model_class, include)
        return select_stmt.options(*load_options)


class R(_R):
    @session_manager()
    async def get[M: Base](
        self, /,
        model: type[M],
        session: AsyncSession | None = None,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _offset: int = 0,
        **kwargs: Any,
    ) -> M | None:
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
            _search_mode:
                Search strategy ("simple" or "engine").
            _search_relevance:
                If ``True``, apply relevance ordering for engine searches.
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
        model_class = ModelClass.from_model(model)
        resolved = require_session(session)

        return await self._get_instance(
            model_class,
            resolved,
            _select=_select,
            _join=_join,
            _where=_where,
            _sorting=_sorting,
            _filters=_filters,
            _search=_search,
            _search_mode=_search_mode,
            _search_relevance=_search_relevance,
            _include=_include,
            _offset=_offset,
            **kwargs,
        )

    @overload
    @session_manager()
    async def get_many[M: Base](
        self, /,
        model: type[M], *,
        session: AsyncSession | None = None,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        _count: Literal[False] = False,
        **kwargs: Any,
    ) -> list[M]: ...

    @overload
    @session_manager()
    async def get_many[M: Base](
        self, /,
        model: type[M], *,
        session: AsyncSession | None = None,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        _count: Literal[True],
        **kwargs: Any,
    ) -> tuple[list[M], int | None]: ...

    @session_manager()
    async def get_many[M: Base](
        self, /,
        model: type[M], *,
        session: AsyncSession | None = None,
        _select: str | Iterable[str] | None = None,
        _join: JoinTargets | None = None,
        _where: WhereClause | None = None,
        _sorting: Sorting | None = None,
        _filters: Filters | None = None,
        _search: str | None = None,
        _search_mode: SearchMode = "simple",
        _search_relevance: bool = False,
        _include: Include | None = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        _reversed: bool = False,
        _count: bool = False,
        **kwargs: Any,
    ) -> list[M] | tuple[list[M], int | None]:
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
            _search_mode:
                Search strategy ("simple" or "engine").
            _search_relevance:
                If ``True``, apply relevance ordering for engine searches.
            _include:
                Nested relationship loading specification.
            _limit:
                Maximum number of rows to return. Clamped between configured bounds.
            _offset:
                Number of rows to skip before returning results.
            _reversed:
                If True, reverses the result list after retrieval.
            _count:
                If True, also returns the total count of matching rows (without limit/offset).
            **kwargs:
                Additional equality filters applied via `filter_by()`.

        Returns:
            A list of matching model instances or projected scalar values.
            If _count is True, returns a tuple of (results, total_count).
        """
        model_class = ModelClass.from_model(model)
        resolved = require_session(session)

        if _count:
            return await self._get_instances(
                model_class,
                resolved,
                _select=_select,
                _join=_join,
                _where=_where,
                _sorting=_sorting,
                _filters=_filters,
                _search=_search,
                _search_mode=_search_mode,
                _search_relevance=_search_relevance,
                _include=_include,
                _limit=_limit,
                _offset=_offset,
                _reversed=_reversed,
                _count=True,
                **kwargs,
            )

        return await self._get_instances(
            model_class,
            resolved,
            _select=_select,
            _join=_join,
            _where=_where,
            _sorting=_sorting,
            _filters=_filters,
            _search=_search,
            _search_mode=_search_mode,
            _search_relevance=_search_relevance,
            _include=_include,
            _limit=_limit,
            _offset=_offset,
            _reversed=_reversed,
            _count=False,
            **kwargs,
        )
