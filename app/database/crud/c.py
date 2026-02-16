from typing import Any

from sqlalchemy.sql import select, and_
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.strategy_options import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseType, ModelClass
from .decorators import session_manager, ensure_required


class _C:
    @staticmethod
    @ensure_required()
    async def _add_instance(
        model_class: ModelClass,
        session: AsyncSession,
        **kwargs
    ) -> BaseType:
        if not kwargs and len(model_class.required_columns) > 0:
            raise ValueError("At least one field must be provided to create an instance")

        model = model_class.value
        valid_attrs = model_class.column_names | model_class.relationship_names

        for key in kwargs:
            if key not in valid_attrs:
                raise ValueError(f"{model.__name__} has no attribute '{key}'")

        instance = await _C._resolve_or_create(model_class, kwargs, session)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)

        return instance

    @staticmethod
    @ensure_required(many=True)
    async def _add_instances(
        model_class: ModelClass,
        session: AsyncSession,
        *data: dict
    ) -> list[BaseType]:
        if not data:
            return []

        model = model_class.value
        valid_attrs = model_class.column_names | model_class.relationship_names
        required_columns_len = len(model_class.required_columns)
        instances = []

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise TypeError(f"Item #{i} must be a dict, got {type(item).__name__}")

            if not item and required_columns_len > 0:
                raise ValueError(f"Item #{i} must contain at least one field")

            for key in item:
                if key not in valid_attrs:
                    raise ValueError(f"{model.__name__} has no attribute '{key}'")

            instance = await _C._resolve_or_create(model_class, item, session)
            instances.append(instance)

        session.add_all(instances)
        await session.flush()

        for instance in instances:
            await session.refresh(instance)

        return instances

    @staticmethod
    async def _resolve_or_create(
        model_class: ModelClass,
        data: dict[str, Any],
        session: AsyncSession,
    ) -> BaseType:
        model = model_class.value
        mapper = model_class.mapper
        pk_keys = [col.key for col in mapper.primary_key]
        column_keys = model_class.column_names
        relationship_keys = model_class.relationship_names
        relationship_loaders = [
            selectinload(getattr(model, rel.key))
            for rel in mapper.relationships
        ]
        instance = None

        # Lookup via primary key
        if all(pk in data for pk in pk_keys):
            identity = tuple(data[pk] for pk in pk_keys)

            if len(identity) == 1:
                identity = identity[0]

            instance = await session.get(model, identity, options=relationship_loaders)

            if instance is not None:
                _C._ensure_same_session(instance, session)

        # Lookup via single/composite constraint
        if instance is None:
            unique_sets: list[list[str]] = []

            for column in mapper.columns:
                if column.unique:
                    unique_sets.append([column.key])

            for constraint in mapper.local_table.constraints:
                if isinstance(constraint, UniqueConstraint):
                    cols = [col.name for col in constraint.columns]
                    unique_sets.append(cols)

            seen = set()
            deduped = []

            for cols in unique_sets:
                key = tuple(cols)

                if key not in seen:
                    seen.add(key)
                    deduped.append(cols)

            for columns in deduped:
                if not all(col in data for col in columns):
                    continue

                for obj in session.identity_map.values():
                    if isinstance(obj, model):
                        if all(getattr(obj, col) == data[col] for col in columns):
                            instance = obj
                            _C._ensure_same_session(instance, session)
                            break

                if instance:
                    break

                conditions = [
                    getattr(model, col) == data[col]
                    for col in columns
                ]

                stmt = (
                    select(model)
                    .where(and_(*conditions))
                    .options(*relationship_loaders)
                )

                instance = await session.scalar(stmt)

                if instance is not None:
                    _C._ensure_same_session(instance, session)
                    break

        # Create if not found
        if instance is None:
            instance = model()

            for key in column_keys:
                if key in data:
                    setattr(instance, key, data[key])

            # Recursively resolve relationships
            for key in relationship_keys:
                if key not in data:
                    continue

                relationship = mapper.relationships[key]
                related_model = relationship.mapper.class_
                related_model_class = ModelClass(related_model)
                value = data[key]

                # One-to-many / many-to-many
                if relationship.uselist:
                    new_items = []

                    for item in value:
                        if isinstance(item, dict):
                            obj = await _C._resolve_or_create(
                                related_model_class,
                                item,
                                session,
                            )
                        else:
                            obj = item
                            _C._ensure_same_session(obj, session)

                        new_items.append(obj)

                    state = inspect(instance)

                    if state.persistent:
                        await session.refresh(instance, attribute_names=[key])

                    setattr(instance, key, new_items)
                # One-to-one / Many-to-one
                else:
                    if isinstance(value, dict):
                        obj = await _C._resolve_or_create(
                            related_model_class,
                            value,
                            session,
                        )
                        setattr(instance, key, obj)
                    else:
                        obj = value
                        _C._ensure_same_session(obj, session)

        return instance

    @staticmethod
    def _ensure_same_session(obj: Any, session: AsyncSession) -> None:
        state = inspect(obj)

        if state.session is not None and state.session is not session.sync_session:
            raise RuntimeError(
                f"Object {obj!r} is bound to a different session.\n"
                f"Object session id: {id(state.session)}\n"
                f"Current session id: {id(session)}\n\n"
                "Please ensure one of the following:\n"
                "   1. The appropriate session was passed into this operation.\n"
                "   2. The object's creating operation committed and the object was reloaded.\n"
                "   3. The same session instance is shared across dependent operations."
            )


class C(_C):
    @session_manager()
    async def add(
        self,
        model: type[BaseType],
        session: AsyncSession = None,
        **kwargs
    ) -> BaseType:
        model_class = ModelClass(model)

        return await self._add_instance(
            model_class,
            session,
            **kwargs
        )

    @session_manager()
    async def add_many(
        self,
        model: type[BaseType],
        *data: dict,
        session: AsyncSession = None
    ) -> list[BaseType]:
        model_class = ModelClass(model)

        return await self._add_instances(
            model_class,
            session,
            *data,
        )
