from sqlalchemy.sql import select, text

from app.database.models import ModelClass, Base
from .decorators import session_manager, session_manager_stream, ensure_required, SessionResolver, db_session_resolver
from .protocol import DatabaseProtocol
from .misc import Misc
from .c import C
from .r import R
from .u import U
from .d import D


class CRUD(C, R, U, D, Misc, DatabaseProtocol):
    """Unified database interface composing CRUD operations.

    This class aggregates CRUD mixins into a single ORM surface that enforces:
        - Explicit query composition and loading semantics
        - Deterministic identity resolution during creation
        - Primary-key-anchored updates
        - Guarded, specificity-enforced deletions
        - Session consistency and unit-of-work integrity

    In addition to CRUD operations, it provides database lifecycle and metadata
    utilities.

    The design favors safety, validation, and predictable behavior over implicit or
    bulk SQL shortcuts.
    """
    async def create_database(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def recreate_database(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def force_clear_database(self):
        async with self.engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))

    async def is_empty(self) -> bool:
        async with self.session() as session:
            for model_class in ModelClass:
                stmt = select(model_class.value).limit(1)
                result = await session.execute(stmt)

                if result.scalars().first() is not None:
                    return False

        return True
