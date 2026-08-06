"""General-purpose utility functions."""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from io import BytesIO


def generate_uuid() -> str:
    """Generate a random UUID hex string.

    Returns:
        A hex-encoded UUID v4 string.
    """
    return uuid.uuid4().hex


def aware_utcnow() -> datetime:
    """Return the current UTC datetime with timezone info.

    Returns:
        An aware datetime in UTC.
    """
    return datetime.now(tz=UTC)


def parse_iso8601(datetime_string: str) -> datetime:
    """Parse an ISO 8601 datetime string.

    Handles all valid ISO 8601 formats including:
    - '2024-01-15T12:00:00Z'
    - '2024-01-15T12:00:00+00:00'
    - '2024-01-15T12:00:00.123456'
    - '2024-01-15T12:00:00.123456Z'
    """
    if not datetime_string:
        return aware_utcnow()
    return datetime.fromisoformat(datetime_string)


def combine_checksums(checksums: list[str]) -> str:
    """Combine multiple checksums into a single MD5 hash.

    Args:
        checksums:
            List of checksum strings to combine.

    Returns:
        The combined MD5 hex digest.
    """
    combined_hash = hashlib.md5()

    for checksum in checksums:
        combined_hash.update(checksum.encode())

    return combined_hash.hexdigest()


async def stream_file(file: BytesIO, chunk_size: int = 1024) -> AsyncGenerator[bytes]:
    """Stream file contents in chunks.

    Args:
        file:
            The BytesIO object to stream.
        chunk_size:
            Size of each chunk in bytes.

    Yields:
        Bytes chunks of the file content.
    """
    file.seek(0)

    while chunk := file.read(chunk_size):
        yield chunk


def clamp(value: int, min_value: int, max_value: int) -> int:
    """Clamp a value between a minimum and maximum.

    Args:
        value:
            The value to clamp.
        min_value:
            The minimum allowed value.
        max_value:
            The maximum allowed value.

    Returns:
        The clamped value.
    """
    return max(min_value, min(value, max_value))


def get_nested_value(data: dict[str, Any], path: str) -> Any:
    """Retrieve a value from a nested dictionary using a dot-separated path.

    Args:
        data:
            The dictionary to traverse.
        path:
            Dot-separated key path (e.g. ``"a.b.c"``).

    Returns:
        The value at the specified path.

    Raises:
        KeyError:
            If a key in the path does not exist.
    """
    keys = path.split(".")
    value = data

    for key in keys:
        if key in value:
            value = value[key]
        else:
            raise KeyError(f"Key '{key}' not found in {value}")

    return value


def parse_user_ids(env_var: str, required: bool = False) -> list[int]:
    """Parse comma-separated user IDs from an environment variable.

    Args:
        env_var:
            Name of the environment variable.
        required:
            Whether at least one ID must be present.

    Returns:
        List of parsed user ID integers.

    Raises:
        ValueError:
            If the value is required but empty, or contains non-integer values.
    """
    value = os.getenv(env_var, "")

    if not value.strip():
        if required:
            raise ValueError(f"{env_var} must be provided in .env (at least one ID)")

        return []
    try:
        return [int(uid.strip()) for uid in value.split(",") if uid.strip()]
    except ValueError as err:
        raise ValueError(f"{env_var} must contain only comma-separated integers") from err
