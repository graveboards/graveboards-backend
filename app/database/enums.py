from enum import Enum

__all__ = [
    "RoleName",
    "RequestStatus"
]


class RoleName(Enum):
    ADMIN = "admin"
    PRIVILEGED = "privileged"


class RequestStatus(Enum):
    REJECTED = -1
    PENDING = 0
    ACCEPTED = 1
