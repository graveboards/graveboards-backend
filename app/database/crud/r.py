from typing import Iterable, Any

from sqlalchemy.sql import select, desc
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm.strategy_options import selectinload, joinedload, noload, defer, Load
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseType, ModelClass, Base
from app.utils import clamp
from .decorators import session_manager
from .types import LoadingStrategy, LoadingOptions, LoadingOptionsConfig

QUERY_MIN_LIMIT = 1
QUERY_MAX_LIMIT = 100
QUERY_DEFAULT_LIMIT = 50


class _R:
    @staticmethod
    async def _get_instance(
            model_class: ModelClass,
            session: AsyncSession,
            **kwargs
    ) -> BaseType:
        select_stmt = _R._construct_stmt(model_class, **kwargs)

        return await session.scalar(select_stmt)

    @staticmethod
    async def _get_instances(
            model_class: ModelClass,
            session: AsyncSession,
            _limit: int = QUERY_DEFAULT_LIMIT,
            _offset: int = 0,
            **kwargs
    ) -> list[BaseType]:
        select_stmt = _R._construct_stmt(model_class, **kwargs)
        select_stmt = select_stmt.limit(clamp(_limit, QUERY_MIN_LIMIT, QUERY_MAX_LIMIT)).offset(_offset)

        return list((await session.scalars(select_stmt)).all())

    @staticmethod
    def _construct_stmt(
            model_class: ModelClass,
            _select: str | Iterable[str] = None,
            _where: Any | Iterable[Any] = None,
            _reversed: bool = False,
            _loading_options: LoadingOptions = None,
            _eager_loads: dict[str, LoadingStrategy] = None,  # Deprecated
            _auto_eager_loads: Iterable[str] = None,  # Deprecated
            _exclude: Iterable[str] = None,
            _exclude_lazy: bool = False,
            **kwargs
    ) -> Select:
        if _eager_loads or _auto_eager_loads:
            raise DeprecationWarning("_eager_loads and _auto_eager_loads are deprecated, use _loading_options instead")
        if _loading_options and (_eager_loads or _auto_eager_loads):
            raise ValueError("_loading_options are mutually exclusive to _eager_loads and _auto_eager_loads")
        if _eager_loads and _auto_eager_loads:
            raise ValueError("_eager_loads and _auto_eager_loads are mutually exclusive")

        if _select is not None:
            if not isinstance(_select, (list, tuple, set)):
                _select = [_select]

            column_map = model_class.value.__annotations__
            targets = []

            for target_name in _select:
                if target_name not in column_map:
                    raise ValueError(f"{target_name} is not a valid column nor relationship of {model_class.value}")

                targets.append(getattr(model_class.value, target_name))

            select_stmt = select(*targets).filter_by(**kwargs)
        else:
            select_stmt = select(model_class.value).filter_by(**kwargs)

        if _where is not None:
            if not isinstance(_where, (list, tuple, set)):
                _where = [_where]

            select_stmt = select_stmt.where(*_where)

        if _reversed:
            select_stmt = _R._apply_reversed(select_stmt, model_class)

        if _loading_options:
            select_stmt = _R._apply_loading_options(select_stmt, model_class, _loading_options)

        if _eager_loads:
            select_stmt = _R._apply_eager_loads(select_stmt, model_class, _eager_loads)

        if _auto_eager_loads:
            select_stmt = _R._apply_auto_eager_loads(select_stmt, model_class, _auto_eager_loads)

        if _exclude:
            select_stmt = _R._apply_exclude(select_stmt, model_class, _exclude)

        if _exclude_lazy:
            select_stmt = _R._apply_exclude_lazy(select_stmt, model_class)

        return select_stmt

    @staticmethod
    def _apply_reversed(select_stmt: Select, model_class: ModelClass) -> Select:
        return select_stmt.order_by(desc(model_class.mapper.primary_key[0]))

    @staticmethod
    def _apply_eager_loads(select_stmt: Select, model_class: ModelClass, eager_loads: dict[str, LoadingStrategy]) -> Select:
        load_options = []

        for attr_name, strategy in eager_loads.items():
            if attr_name in model_class.mapper.relationships:
                attr = model_class.mapper.attrs[attr_name]

                if strategy == "joinedload":
                    load_options.append(joinedload(attr))
                elif strategy == "selectinload":
                    load_options.append(selectinload(attr))
                else:
                    raise ValueError(f"Unsupported loading strategy: {strategy}")
            else:
                raise ValueError(f"{attr_name} is not a valid relationship in {model_class.value}")

        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_auto_eager_loads(select_stmt: Select, model_class: ModelClass, relationships: Iterable[str]) -> Select:
        load_options = []

        for attr_name in relationships:
            if attr_name in model_class.mapper.relationships:
                attr = model_class.mapper.attrs[attr_name]
                is_collection = model_class.mapper.relationships[attr_name].uselist

                if is_collection:
                    load_options.append(selectinload(attr))
                else:
                    load_options.append(joinedload(attr))
            else:
                raise ValueError(f"{attr_name} is not a valid relationship in {model_class.value}")

        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_loading_options(select_stmt: Select, model_class: ModelClass, loading_options: LoadingOptions) -> Select:
        def parse_node(attr_name: str, config: LoadingOptionsConfig, parent_model_class: ModelClass) -> Load:
            if attr_name not in parent_model_class.mapper.relationships:
                raise ValueError(f"{attr_name} is not a valid relationship in {parent_model_class.value}")

            attr = parent_model_class.mapper.attrs[attr_name]
            rel_info = parent_model_class.mapper.relationships[attr_name]
            target_model_class = ModelClass(rel_info.mapper.class_)

            if config is True:
                strategy = "selectinload" if rel_info.uselist else "joinedload"
                children = None
            elif config is False:
                strategy = "noload"
                children = None
            elif isinstance(config, str):
                strategy = config
                children = None
            elif isinstance(config, dict):
                strategy = config.get("strategy")
                children = config.get("options")

                if strategy is None:
                    strategy = "selectinload" if rel_info.uselist else "joinedload"
            else:
                raise ValueError(f"Invalid config for relationship '{attr_name}': {config}")

            if strategy == "joinedload":
                loader = joinedload(attr)
            elif strategy == "selectinload":
                loader = selectinload(attr)
            elif strategy == "noload":
                loader = noload(attr)
            else:
                raise ValueError(f"Unsupported loading strategy: {strategy}")

            if children and strategy != "noload":
                for child_attr, child_config in children.items():
                    loader = loader.options(parse_node(child_attr, child_config, target_model_class))

            return loader

        load_options = [parse_node(attr, config, model_class) for attr, config in loading_options.items()]
        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_exclude(select_stmt: Select, model_class: ModelClass, exclude: Iterable[str]) -> Select:
        load_options = []

        for attr_name in exclude:
            if attr_name in model_class.mapper.columns:
                attr = model_class.mapper.attrs[attr_name]
                load_options.append(defer(attr))
            elif attr_name in model_class.mapper.relationships:
                attr = model_class.mapper.attrs[attr_name]
                load_options.append(noload(attr))
            else:
                raise ValueError(f"{attr_name} is not a valid column nor relationship in {model_class.value}")

        return select_stmt.options(*load_options)


    @staticmethod
    def _apply_exclude_lazy(select_stmt: Select, model_class: ModelClass) -> Select:
        noload_relationships = [
            noload(attr)
            for attr in model_class.mapper.relationships
            if attr.lazy is True or attr.lazy in {"select", "dynamic", "raise_on_sql"}
        ]

        return select_stmt.options(*noload_relationships)


class R(_R):
    @session_manager
    async def get(
        self,
        model: type[BaseType],
        session: AsyncSession = None,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _order_by: Union[Any, Iterable[Any]] = None,
        _reversed: bool = False,
        _include: Include = None,
        _offset: int = 0,
        **kwargs
    ) -> Optional[BaseType]:
        model_class = ModelClass(model)

        return await self._get_instance(
            model_class,
            session,
            _select=_select,
            _join=_join,
            _where=_where,
            _order_by=_order_by,
            _reversed=_reversed,
            _include=_include,
            _offset=_offset,
            **kwargs
        )

    @session_manager
    async def get_many(
        self,
        model: type[BaseType],
        session: AsyncSession = None,
        _select: Union[str, Iterable[str]] = None,
        _join: Union[Any, Iterable[Any]] = None,
        _where: Union[Any, Iterable[Any]] = None,
        _order_by: Union[Any, Iterable[Any]] = None,
        _reversed: bool = False,
        _include: Include = None,
        _limit: int = QUERY_DEFAULT_LIMIT,
        _offset: int = 0,
        **kwargs
    ) -> list[BaseType]:
        model_class = ModelClass(model)

        return await self._get_instances(
            model_class,
            session,
            _select=_select,
            _join=_join,
            _where=_where,
            _order_by=_order_by,
            _reversed=_reversed,
            _include=_include,
            _limit=_limit,
            _offset=_offset,
            **kwargs
        )
