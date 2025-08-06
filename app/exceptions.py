from datetime import datetime
from typing import Any


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
        return f"Category {self.category} does not support field '{self.field}'"


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
    def __init__(self, title: str):
        self.title = title

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"All {self.title} values cannot be None"


class RestrictedUserError(ValueError):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __str__(self):
        return self.message

    @property
    def message(self) -> str:
        return f"User {self.user_id} is either restricted, deleted, or otherwise inaccessible"


class RateLimitExceeded(Exception):
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
