from datetime import datetime
from typing import Any, Sequence

from authlib.integrations.base_client.errors import OAuthError
from connexion.exceptions import BadRequestProblem, ClientProblem

__all__ = [
    "TypeValidationError",
    "FieldValidationError",
    "FieldNotSupportedError",
    "FieldConditionValidationError",
    "UnknownFieldCategoryError",
    "AllValuesNullError",
    "RestrictedUserError",
    "RateLimitExceededError",
    "RedisLockTimeoutError",
    "ArrayValidationError",
    "DeepObjectValidationError",
    "BadRequest",
    "NotFound",
    "Conflict",
    "OsuOAuthError",
    "bad_request_factory"
]


class TypeValidationError(TypeError):
    def __init__(self, value_type: type, *target_types: type):
        self.value_type = value_type
        self.target_types = target_types

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"Expected type(s) {self.expected_types}, but got {self.value_type.__name__}"

    @property
    def expected_types(self) -> str:
        return ", ".join(t.__name__ for t in self.target_types)


class FieldValidationError(TypeValidationError):
    def __init__(
        self,
        category: str,
        field: str,
        value: Any,
        *target_types: type
    ):
        self.category = category
        self.field = field
        self.value = value

        super().__init__(type(self.value), *target_types)

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return (
            f"Field '{self.field}' in category '{self.category}' received value {repr(self.value)} "
            f"of type {self.value_type.__name__}, expected type(s): {self.expected_types}"
        )


class FieldNotSupportedError(Exception):
    def __init__(self, category: str, field: str):
        self.category = category
        self.field = field
        
    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"Category '{self.category}' does not support field '{self.field}'"


class FieldConditionValidationError(Exception):
    def __init__(self, category: str, field: str, detail: str):
        self.category = category
        self.field = field
        self.detail = detail

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"Invalid conditions for field '{self.field}' in category '{self.category}': {self.detail}"


class UnknownFieldCategoryError(Exception):
    def __init__(self, category: str):
        self.category = category

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"Unknown field category '{self.category}'"


class AllValuesNullError(Exception):
    def __init__(self, origin: str):
        self.origin = origin

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"All {self.origin} values cannot be None"


class RestrictedUserError(ValueError):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"User {self.user_id} is either restricted, deleted, or otherwise inaccessible"


class RateLimitExceededError(Exception):
    def __init__(self, next_window: datetime):
        self.next_window = next_window

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"Rate limit exceeded. Try again in {self.remaining_time:.2f} seconds."

    @property
    def remaining_time(self) -> float:
        return (self.next_window - datetime.now()).total_seconds()


class RedisLockTimeoutError(TimeoutError):
    def __init__(self, key: str, timeout: float):
        self.key = key
        self.timeout = timeout

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"Could not acquire lock for '{self.key}' after {self.timeout} seconds"


class ArrayValidationError(ValueError):
    def __init__(self, index: int, message: str):
        self.index = index
        self.message = message
        super().__init__(f"At index {index}: {message}")


class DeepObjectValidationError(ValueError):
    def __init__(self, path: Sequence[str], message: str):
        self.path = path
        self.message = message
        super().__init__(f"{'.'.join(path)}: {message}")


class BadRequest(BadRequestProblem):
    def __init__(self, detail: str, path: Sequence[str] = None):
        super().__init__(detail=detail)

        if path:
            self.ext = {"path": ".".join(path)}


class NotFound(ClientProblem):
    def __init__(self, detail: str, path: Sequence[str] = None):
        super().__init__(status=404, title="Not Found", detail=detail)

        if path:
            self.ext = {"path": ".".join(path)}


class Conflict(ClientProblem):
    def __init__(self, detail: str, path: Sequence[str] = None):
        super().__init__(status=409, title="Conflict", detail=detail)

        if path:
            self.ext = {"path": ".".join(path)}


class OsuOAuthError(BadRequest):
    def __init__(self, e: OAuthError):
        if not isinstance(e, OAuthError):
            raise TypeError(f"Parameter e must be OAuthError, got {type(e)}")

        super().__init__(e.description)
        self.title = "osu! OAuth Error"
        self.ext = {"oauth_error": e.error}

        if e.error == "invalid_request":
            self.ext["hint"] = "The authorization code may have already been used, expired, or the state parameter does not match"


def bad_request_factory(e: Exception) -> BadRequest:
    message = getattr(e, "message", str(e))
    path = getattr(e, "path", None)
    return BadRequest(message, path=path)
