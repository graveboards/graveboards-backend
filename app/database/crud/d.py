from typing import Iterable

from sqlalchemy.sql import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import and_

from app.database.models import BaseType, ModelClass
from .decorators import session_manager


class _D:
    @staticmethod
    async def _delete_instance(
        model_class: ModelClass,
        session: AsyncSession,
        **kwargs
    ):
        if not kwargs:
            raise ValueError("At least one filter must be provided to delete an instance")

        model = model_class.value

        for key in kwargs:
        select_stmt = select(model_class.value).filter_by(**kwargs)

        rows = (await session.scalars(select_stmt)).all()

        if not rows:
            raise ValueError(f"No {model.__name__} matches the provided filters")

        if len(rows) > 1:
            raise ValueError(f"Delete would affect {len(rows)} rows; filters are not specific enough")

        await session.delete(rows[0])
        await session.commit()

    @staticmethod
    async def _delete_instances(
        model_class: ModelClass,
        session: AsyncSession,
        **kwargs
    ) -> int:
        if not kwargs:
            raise ValueError("At least one filter must be provided to delete instances")

        model = model_class.value
        conditions = []

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

        await session.commit()
        return len(rows)


class D(_D):
    @session_manager
    async def delete(
        self,
        model: type[BaseType],
        session: AsyncSession = None,
        **kwargs
    ):
        model_class = ModelClass(model)

        await self._delete_instance(
            model_class,
            session,
            **kwargs
        )

    @session_manager
    async def delete_many(
            self,
            model: type[BaseType],
            session: AsyncSession = None,
            **kwargs
    ) -> int:
        model_class = ModelClass(model)

        return await self._delete_instances(
            model_class,
            session,
            **kwargs
        )
