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

        instance = model(**kwargs)
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

            instances.append(model(**item))

        session.add_all(instances)
        await session.flush()

        for instance in instances:
            await session.refresh(instance)

        return instances


class C(_C):
    @session_manager
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

    @session_manager
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
