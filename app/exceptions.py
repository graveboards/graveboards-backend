"""Custom application exceptions and error types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from authlib.integrations.base_client.errors import OAuthError
from connexion.exceptions import BadRequestProblem, ClientProblem

from app.utils import aware_utcnow

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from app.database.models import BaseType

__all__ = [
    "AllValuesNullError",
    "ArrayValidationError",
    "BadRequest",
    "Conflict",
    "DeepObjectValidationError",
    "FieldConditionValidationError",
    "FieldNotSupportedError",
    "FieldValidationError",
    "NotFound",
    "OsuOAuthError",
    "RateLimitExceededError",
    "RedisLockTimeoutError",
    "RestrictedUserError",
    "TooManyRequests",
    "TypeValidationError",
    "UnknownFieldCategoryError",
    "bad_request_factory",
    "clean_error_msg",
]


class TypeValidationError(TypeError):
    """Validation error for unexpected value types.

    Attributes:
        value_type:
            The actual type that was received.
        target_types:
            The expected types.
    """

    def __init__(self, value_type: type, *target_types: type):
        self.value_type = value_type
        self.target_types = target_types

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"Expected type(s) {self.expected_types}, but got {self.value_type.__name__}"

    @property
    def expected_types(self) -> str:
        """The expected types as a comma-separated string."""
        return ", ".join(t.__name__ for t in self.target_types)


class FieldValidationError(TypeValidationError):
    """Validation error for an invalid field value.

    Attributes:
        model:
            The model class containing the field.
        field:
            The field name that failed validation.
        value:
            The invalid value.
    """

    def __init__(self, model: type[BaseType], field: str, value: Any, *target_types: type):
        self.model = model
        self.field = field
        self.value = value

        super().__init__(type(self.value), *target_types)

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return (
            f"Field '{self.field}' of model '{self.model.__name__}' received value {self.value!r} "
            f"of type {self.value_type.__name__}, expected type(s): {self.expected_types}"
        )


class FieldNotSupportedError(Exception):
    """Error raised when a model does not support a requested field.

    Attributes:
        model:
            The model class.
        field:
            The unsupported field name.
    """

    def __init__(self, model: type[BaseType], field: str):
        self.model = model
        self.field = field

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"Model '{self.model.__name__}' does not support field '{self.field}'"


class FieldConditionValidationError(Exception):
    """Error raised for invalid conditions on a model field.

    Attributes:
        model:
            The model class.
        field:
            The field with invalid conditions.
        detail:
            Additional details about the validation failure.
    """

    def __init__(self, model: type[BaseType], field: str, detail: str):
        self.model = model
        self.field = field
        self.detail = detail

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"Invalid conditions for field '{self.field}' of model '{self.model.__name__}': {self.detail}"


class UnknownFieldCategoryError(Exception):
    """Error raised when an unknown field category is encountered.

    Attributes:
        category:
            The unknown category name.
    """

    def __init__(self, category: str):
        self.category = category

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"Unknown field category '{self.category}'"


class AllValuesNullError(Exception):
    """Error raised when all values in a collection are None.

    Attributes:
        origin:
            The source of the null values.
    """

    def __init__(self, origin: str):
        self.origin = origin

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"All {self.origin} values cannot be None"


class RestrictedUserError(ValueError):
    """Error raised when a user is restricted, deleted, or inaccessible.

    Attributes:
        user_id:
            The ID of the restricted user.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"User {self.user_id} is either restricted, deleted, or otherwise inaccessible"


class RateLimitExceededError(Exception):
    """Error raised when an API rate limit has been exceeded.

    Attributes:
        next_window:
            The time at which the rate limit window resets.
        last_call_timestamp:
            Timestamp of the last API call.
    """

    def __init__(
        self, next_window: datetime | None = None, last_call_timestamp: float | None = None
    ):
        self.next_window = next_window
        self.last_call_timestamp = last_call_timestamp

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        parts = ["Rate limit exceeded"]
        if self.last_call_timestamp is not None:
            parts.append(f"Last call: {self.last_call_timestamp}")
        if self.next_window is not None:
            parts.append(f"Try again in {self.remaining_time:.2f} seconds.")
        return ". ".join(parts)

    @property
    def remaining_time(self) -> float:
        """The time remaining until the rate limit resets.

        Returns:
            The remaining time in seconds, or 0.0 if no window is set.
        """
        if self.next_window is None:
            return 0.0
        return (self.next_window - aware_utcnow()).total_seconds()


class RedisLockTimeoutError(TimeoutError):
    """Error raised when a Redis distributed lock cannot be acquired.

    Attributes:
        key:
            The lock key that could not be acquired.
        timeout:
            The timeout duration in seconds.
    """

    def __init__(self, key: str, timeout: float):
        self.key = key
        self.timeout = timeout

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"Could not acquire lock for '{self.key}' after {self.timeout} seconds"


class ArrayValidationError(ValueError):
    """Error raised for validation failures in array fields.

    Attributes:
        index:
            The array index where validation failed.
        message:
            The validation error message.
    """

    def __init__(self, index: int, message: str):
        self.index = index
        self._message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"At index {self.index}: {self._message}"


class DeepObjectValidationError(ValueError):
    """Error raised for validation failures in deep object paths.

    Attributes:
        path:
            The dot-separated path where validation failed.
        message:
            The validation error message.
    """

    def __init__(self, path: Sequence[str], message: str):
        self.path = path
        self._message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        """The error message."""
        return f"{'.'.join(self.path)}: {self._message}"


class BadRequest(BadRequestProblem):
    """Custom 400 Bad Request exception with optional path info."""

    def __init__(self, detail: str, path: Sequence[str] | None = None):
        super().__init__(detail=detail)

        if path:
            self.ext = {"path": ".".join(path)}


class NotFound(ClientProblem):
    """Custom 404 Not Found exception with optional path info."""

    def __init__(self, detail: str, path: Sequence[str] | None = None):
        super().__init__(status=404, title="Not Found", detail=detail)

        if path:
            self.ext = {"path": ".".join(path)}


class Conflict(ClientProblem):
    """Custom 409 Conflict exception with optional path info."""

    def __init__(self, detail: str, path: Sequence[str] | None = None):
        super().__init__(status=409, title="Conflict", detail=detail)

        if path:
            self.ext = {"path": ".".join(path)}


class OsuOAuthError(BadRequest):
    """Error raised for osu! OAuth authentication failures.

    Attributes:
        e:
            The underlying OAuthError.
    """

    def __init__(self, e: OAuthError):
        if not isinstance(e, OAuthError):
            raise TypeError(f"Parameter e must be OAuthError, got {type(e)}")

        super().__init__(e.description)
        self.title = "osu! OAuth Error"
        self.ext = {"oauth_error": e.error}

        if e.error == "invalid_request":
            self.ext["hint"] = (
                "The authorization code may have already been used, expired, or the state parameter does not match"
            )


class TooManyRequests(ClientProblem):
    """Custom 429 Too Many Requests exception."""

    def __init__(self, detail: str):
        super().__init__(status=429, title="Too Many Requests", detail=detail)


def bad_request_factory(e: Exception) -> BadRequest:
    """Convert an exception to a BadRequest instance.

    Args:
        e:
            The exception to convert.

    Returns:
        A BadRequest instance with the exception's message and path.
    """
    message = getattr(e, "message", str(e))
    path = getattr(e, "path", None)
    if path is not None:
        return BadRequest(message, path=path)
    return BadRequest(message)


def clean_error_msg(e: Exception) -> str:
    """Strip noisy MDN reference links from HTTP error messages."""
    msg = str(e)
    if "For more information check:" in msg:
        msg = msg.split("For more information check:")[0].rstrip()
    return msg
