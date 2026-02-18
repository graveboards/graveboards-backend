from typing import Iterable, Any, Optional, Union

from sqlalchemy.sql import select
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy.orm.relationships import RelationshipProperty, Relationship
from sqlalchemy.orm.strategy_options import selectinload, joinedload, noload, Load
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseType, ModelClass, Base
from app.utils import clamp
from .decorators import session_manager
from .types import Include, Sorting

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
        _sorting: Union[Any, Iterable[Any]] = None,
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
                Column name or iterable of column names to project. If omitted, selects
                the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
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
        select_stmt = _R._construct_stmt(model_class, _select, _join, _where, _sorting, _include, **kwargs)
        select_stmt = select_stmt.offset(_offset)

        return await session.scalar(select_stmt)

    @staticmethod
    async def _get_instances(
        model_class: ModelClass,
        session: AsyncSession,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _sorting: Union[Any, Iterable[Any]] = None,
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
                Column name or iterable of column names to project. If omitted, selects
                the full model entity.
            _join:
                Join target(s) which may be a model class, a (model, condition) tuple,
                or an iterable of either.
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration as a list of sorting dicts.
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
        select_stmt = _R._construct_stmt(model_class, _select, _join, _where, _sorting, _include, **kwargs)
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
        _include: Include = None,
        **kwargs
    ) -> Select:
        """Construct a SQLAlchemy ``Select`` statement from query parameters.

        This method orchestrates projection, joins, filtering, sorting, relationship
        loading, and lazy-exclusion rules into a single ``Select`` object.

        Args:
            model_class:
                Wrapped model metadata for validation and attribute access.
            _select:
                Column name(s) to project. If omitted, selects full model entity.
            _join:
                Join target(s).
            _where:
                WHERE clause expression(s).
            _sorting:
                Sorting configuration.
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

        if _include and not _select:
            select_stmt, included_paths = _R._apply_include(select_stmt, model_class, _include)

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

        Sorting items must follow the format:
            {"field": "Model.field_name", "order": "asc" | "desc"}

        Only model columns and hybrid properties are sortable.

        Args:
            select_stmt:
                The base ``Select`` statement.
            model_class:
                Wrapped model metadata for validation.
            sorting:
                List of sorting configuration dictionaries.

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
    def _apply_include(
        select_stmt: Select,
        model_class: ModelClass,
        include: Include
    ) -> tuple[Select, set[str]]:
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
                Nested dictionary describing relationships to include.

        Returns:
            A tuple of:
                - The ``Select`` statement with loader options applied.
                - A set of included relationship paths.
        """
        included_paths: set[str] = set()

        def parse_node(
            attr: QueryableAttribute,
            rel_info: RelationshipProperty,
            target_model_class: ModelClass,
            value: Union[bool, Include],
            path: str
        ) -> LoaderOption:
            included_paths.add(path)

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
        return select_stmt.options(*load_options), included_paths

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
        _sorting: Union[Any, Iterable[Any]] = None,
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
        _sorting: Union[Any, Iterable[Any]] = None,
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
            _include=_include,
            _limit=_limit,
            _offset=_offset,
            _reversed=_reversed,
            **kwargs
        )
