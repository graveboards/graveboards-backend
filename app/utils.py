import uuid
import hashlib
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any


def generate_uuid() -> str:
    return uuid.uuid4().hex


def aware_utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def parse_iso8601(datetime_string) -> datetime:
    if datetime_string.endswith("Z"):
        return datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S%z")
    elif "+" in datetime_string:
        return datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S%z")
    else:
        return datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S")


def combine_checksums(checksums: list[str]) -> str:
    combined_hash = hashlib.md5()

    for checksum in checksums:
        combined_hash.update(checksum.encode())

    return combined_hash.hexdigest()


async def stream_file(file: BytesIO, chunk_size: int = 1024):
    file.seek(0)

    while chunk := file.read(chunk_size):
        yield chunk


def clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(value, max_value))


def get_nested_value(data: dict[str, Any], path: str) -> Any:
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"Key '{key}' not found in {value}")

    return value


def parse_user_ids(env_var: str, required: bool = False) -> list[int]:
    value = os.getenv(env_var, "")

    if not value.strip():
        if required:
            raise ValueError(f"{env_var} must be provided in .env (at least one ID)")

        return []
    try:
        return [int(uid.strip()) for uid in value.split(",") if uid.strip()]
    except ValueError:
        raise ValueError(f"{env_var} must contain only comma-separated integers")
