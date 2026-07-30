from __future__ import annotations
from collections.abc import Iterable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from sqlalchemy.sql.elements import and_

from app.database.models import BaseType, ModelClass

from .decorators import require_session, session_manager
from .helpers import validate_model_attrs


class _D:
    @staticmethod
    async def _delete_instance(
        model_class: ModelClass[Any], session: AsyncSession, **kwargs: Any
    ) -> None:
        """Delete a single model instance matching strict filter criteria.

        Performs attribute validation, executes a filtered SELECT to resolve matching
        instances, and deletes exactly one row. If zero or multiple rows match, the
        operation fails to prevent unintended mass deletion.

        This method intentionally avoids raw SQL DELETE statements to preserve ORM
        lifecycle behavior and cascade semantics.

        Args:
            model_class:
                Wrapped model metadata used for validation.
            session:
                Active async SQLAlchemy session.
            **kwargs:
                Equality-based filters used to uniquely identify the instance to delete.

        Raises:
            ValueError:
                If no filters are provided.
            ValueError:
                If an invalid attribute is supplied.
            ValueError:
                If no rows match the filters.
            ValueError:
                If multiple rows match the filters.
        """
        if not kwargs:
            raise ValueError("At least one filter must be provided to delete an instance")

        model = model_class.value
        valid_attrs = model_class.column_names | model_class.hybrid_property_names

        validate_model_attrs(model.__name__, kwargs, valid_attrs)

        select_stmt = select(model_class.value).filter_by(**kwargs)

        rows = (await session.scalars(select_stmt)).all()

        if not rows:
            raise ValueError(f"No {model.__name__} matches the provided filters")

        if len(rows) > 1:
            raise ValueError(
                f"Delete would affect {len(rows)} rows; filters are not specific enough"
            )

        await session.delete(rows[0])
        await session.flush()

    @staticmethod
    async def _delete_instances(
        model_class: ModelClass[Any], session: AsyncSession, **kwargs: Any
    ) -> int:
        """Delete multiple model instances matching filter criteria.

        Supports equality filters and iterable-based membership filters (translated into
        SQL IN clauses). Instances are loaded and deleted through the ORM to preserve
        cascade behavior and session integrity.

        Args:
            model_class:
                Wrapped model metadata used for validation.
            session:
                Active async SQLAlchemy session.
            **kwargs:
                Filtering criteria. Iterable values (excluding strings and bytes) are
                treated as membership filters.

        Returns:
            The number of rows deleted. Returns 0 if no rows match.

        Raises:
            ValueError:
                If no filters are provided.
            ValueError:
                If an invalid attribute is supplied.
        """
        if not kwargs:
            raise ValueError("At least one filter must be provided to delete instances")

        model = model_class.value
        valid_attrs = model_class.column_names | model_class.hybrid_property_names
        conditions = []

        validate_model_attrs(model.__name__, kwargs, valid_attrs)

        for key, value in kwargs.items():
            attr = getattr(model, key)

            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                if not (values := list(value)):
                    return 0

                conditions.append(attr.in_(values))
            else:
                conditions.append(attr == value)

        select_stmt = select(model).where(and_(*conditions))
        rows = (await session.scalars(select_stmt)).all()

        if not rows:
            return 0

        for row in rows:
            await session.delete(row)

        await session.flush()
        return len(rows)


class D(_D):
    @session_manager()
    async def delete(
        self, /, model: type[BaseType], session: AsyncSession | None = None, **kwargs: Any
    ) -> None:
        """Public API for deleting a single model instance.

        Wraps ``_delete_instance`` and manages session lifecycle via the
        ``session_manager`` decorator.

        Args:
            model:
                SQLAlchemy model class.
            session:
                Optional externally managed async session.
            **kwargs:
                Equality-based filters used to uniquely identify the instance to delete.
        """
        model_class = ModelClass.from_model(model)
        resolved = require_session(session)

        await self._delete_instance(model_class, resolved, **kwargs)

    @session_manager()
    async def delete_many(
        self, /, model: type[BaseType], session: AsyncSession | None = None, **kwargs: Any
    ) -> int:
        """Public API for deleting multiple model instances.

        Wraps ``_delete_instances`` and manages session lifecycle via the
        ``session_manager`` decorator.

        Args:
            model:
                SQLAlchemy model class.
            session:
                Optional externally managed async session.
            **kwargs:
                Filtering criteria. Iterable values are treated as membership filters.

        Returns:
            The number of rows deleted.
        """
        model_class = ModelClass.from_model(model)
        resolved = require_session(session)

        return await self._delete_instances(model_class, resolved, **kwargs)
