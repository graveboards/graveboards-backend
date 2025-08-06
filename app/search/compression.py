import base64
import binascii
import json
from typing import Any

import brotli


def compress_query(q: bytes | dict[str, Any], serialized: bool = True) -> str:
    if not isinstance(q, (bytes, dict)):
        raise TypeError(f"q must be bytes or dict, got {type(q).__name__}")

    if serialized:
        compressed = brotli.compress(q)
    else:
        json_str = json.dumps(q)
        compressed = brotli.compress(json_str.encode())

    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return encoded.rstrip("=")


def decompress_query(q: str, serialized: bool = True) -> bytes | dict[str, Any]:
    if not isinstance(q, str):
        raise TypeError(f"q must be str, got {type(q).__name__}")

    try:
        padded = q + ("=" * (len(q) % 4))
        compressed = base64.urlsafe_b64decode(padded)

        if serialized:
            decompressed = brotli.decompress(compressed)
        else:
            json_str = brotli.decompress(compressed).decode()
            decompressed = json.loads(json_str)

        return decompressed
    except (binascii.Error, brotli.error, json.JSONDecodeError):
        raise ValueError("Could not decompress query, ensure it's valid and complete")
