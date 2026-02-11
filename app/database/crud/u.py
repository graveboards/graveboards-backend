from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseType, ModelClass
from .decorators import session_manager


class _U:
    @staticmethod
    async def _update_instance(
        model_class: ModelClass,
        session: AsyncSession,
        primary_key: int,
        **kwargs
    ) -> BaseType:
        if not kwargs:
            raise ValueError("At least one field must be provided to update an instance")

        if not isinstance(primary_key, int):
            raise TypeError(f"Primary key must be int, got {type(primary_key).__name__}")

        model = model_class.value
        valid_attrs = model_class.column_names | model_class.relationship_names
        instance = await session.get(model, primary_key)

        if instance is None:
            raise ValueError(f"There is no {model.__name__} with the primary key '{primary_key}'")

        for key, value in kwargs.items():
            if key not in valid_attrs:
                raise ValueError(f"{model.__name__} has no attribute '{key}'")

            setattr(instance, key, value)

        await session.commit()
        await session.refresh(instance)

        return instance

    @staticmethod
    async def _update_instances(
        model_class: ModelClass,
        session: AsyncSession,
        *data: tuple[int, dict[str, Any]]
    ) -> list[BaseType]:
        if not data:
            return []

        for i, item in enumerate(data):
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError(f"Update #{i} must be a tuple of (int, dict), got {type(item).__name__}")

            pk, delta = item

            if not isinstance(pk, int):
                raise TypeError(f"Primary key in update #{i} must be int, got {type(pk).__name__}")

            if not isinstance(delta, dict):
                raise TypeError(f"Delta in update #{i} must be dict, got {type(delta).__name__}")

        model = model_class.value
        valid_attrs = model_class.column_names | model_class.relationship_names
        instances = []

        for pk, delta in data:
            instance = await session.get(model, pk)

            if instance is None:
                raise ValueError(f"There is no {model.__name__} with the primary key '{pk}'")

            for key, value in delta.items():
                if key not in valid_attrs:
                    raise ValueError(f"{model.__name__} has no attribute '{key}'")

                setattr(instance, key, value)

            instances.append(instance)

        await session.commit()

        for instance in instances:
            await session.refresh(instance)

        return instances


class U(_U):
    @session_manager
    async def update(
        self,
        model: type[BaseType],
        primary_key: int,
        session: AsyncSession = None,
        **kwargs
    ) -> BaseType:
        model_class = ModelClass(model)

        return await self._update_instance(
            model_class,
            session,
            primary_key,
            **kwargs
        )

    @session_manager
    async def update_many(
        self,
        model: type[BaseType],
        *data: tuple[int, dict[str, Any]],
        session: AsyncSession = None
    ) -> BaseType:
        model_class = ModelClass(model)

        return await self._update_instance(
            model_class,
            session,
            *data
        )
