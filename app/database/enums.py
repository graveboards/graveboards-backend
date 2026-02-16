from enum import Enum

__all__ = [
    "RoleName",
    "RequestStatus"
]


class RoleName(Enum):  # TODO: Add base user class to distinguish between internal and external users
    ADMIN = "admin"


class RequestStatus(Enum):
    REJECTED = -1
    PENDING = 0
    ACCEPTED = 1
