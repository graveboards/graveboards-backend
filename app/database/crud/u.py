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
        """Update a single model instance by primary key.

        Performs strict primary key lookup, validates provided attributes, applies
        in-memory mutations, and flushes changes to the database.

        This method does not support conditional or bulk SQL updates—it operates on a
        loaded ORM instance to preserve relationship semantics and session integrity.

        Args:
            model_class:
                Wrapped model metadata used for validation.
            session:
                Active async SQLAlchemy session.
            primary_key:
                Integer primary key identifying the instance.
            **kwargs:
                Field updates to apply. May include column or relationship attributes.

        Returns:
            The updated and refreshed model instance.

        Raises:
            ValueError:
                If no update fields are provided or if the instance does not exist.
            TypeError:
                If the primary key is not an integer.
            ValueError:
                If an invalid attribute is supplied.
        """
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

        await session.flush()
        await session.refresh(instance)

        return instance

    @staticmethod
    async def _update_instances(
        model_class: ModelClass,
        session: AsyncSession,
        *data: tuple[int, dict[str, Any]]
    ) -> list[BaseType]:
        """Update multiple model instances by primary key.

        Each update is provided as a tuple of: (primary_key, delta_dict)

        All updates are validated before execution. Instances are loaded individually,
        mutated in memory, flushed, and refreshed before returning.

        Args:
            model_class:
                Wrapped model metadata used for validation.
            session:
                Active async SQLAlchemy session.
            *data:
                One or more (int, dict) tuples describing updates.

        Returns:
            A list of updated model instances.

        Raises:
            TypeError:
                If any update item is not a (int, dict) tuple.
            ValueError:
                If a referenced instance does not exist.
            ValueError:
                If an invalid attribute is supplied.
        """
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

        await session.flush()

        for instance in instances:
            await session.refresh(instance)

        return instances


class U(_U):
    @session_manager()
    async def update(
        self,
        model: type[BaseType],
        primary_key: int,
        session: AsyncSession = None,
        **kwargs
    ) -> BaseType:
        """Public API for updating a single model instance.

        Wraps ``_update_instance`` and manages session lifecycle via
        the ``session_manager`` decorator.

        Args:
            model:
                SQLAlchemy model class.
            primary_key:
                Integer primary key identifying the instance.
            session:
                Optional externally managed async session.
            **kwargs:
                Field updates to apply.

        Returns:
            The updated model instance.
        """
        model_class = ModelClass(model)

        return await self._update_instance(
            model_class,
            session,
            primary_key,
            **kwargs
        )

    @session_manager()
    async def update_many(
        self,
        model: type[BaseType],
        *data: tuple[int, dict[str, Any]],
        session: AsyncSession = None
    ) -> list[BaseType]:
        """Public API for updating multiple model instances.

        Wraps ``_update_instances`` and manages session lifecycle via
        the ``session_manager`` decorator.

        Args:
            model:
                SQLAlchemy model class.
            *data:
                One or more (int, dict) tuples describing updates.
            session:
                Optional externally managed async session.

        Returns:
            A list of updated model instances.
        """
        model_class = ModelClass(model)

        return await self._update_instances(
            model_class,
            session,
            *data
        )
