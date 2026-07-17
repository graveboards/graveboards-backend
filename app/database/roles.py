from typing import TYPE_CHECKING, Iterable

from app.database.enums import RoleName
from app.database.models import User

if TYPE_CHECKING:
    from app.database import PostgresqlDB

__all__ = ["get_user_roles", "user_has_any_role", "is_admin"]


async def get_user_roles(db: "PostgresqlDB", user_id: int | None) -> set[RoleName]:
    """Fetch the set of roles held by ``user_id``.

    Returns an empty set if ``user_id`` is ``None`` or matches no user.
    """
    if user_id is None:
        return set()

    user = await db.get(User, id=user_id, _include={"roles": True})

    return {RoleName(role.name) for role in user.roles} if user else set()


async def user_has_any_role(db: "PostgresqlDB", user_id: int | None, roles: Iterable[RoleName]) -> bool:
    """Check whether ``user_id`` holds at least one of ``roles``."""
    user_roles = await get_user_roles(db, user_id)

    return bool(user_roles & set(roles))


async def is_admin(db: "PostgresqlDB", user_id: int | None) -> bool:
    """Check whether ``user_id`` has the admin role.

    Admins are expected to bypass ownership/visibility filtering wherever this
    check is used.
    """
    return await user_has_any_role(db, user_id, (RoleName.ADMIN,))
