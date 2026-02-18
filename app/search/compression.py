import base64
import binascii
import json
from typing import Any

import brotli


def compress_query(q: bytes | dict[str, Any], serialized: bool = True) -> str:
    """Compresses and URL-safe encodes a query payload.

    Supports either raw bytes or a JSON-serializable dictionary. The result is
    Brotli-compressed and base64 URL-safe encoded with padding removed.

    Args:
        q:
            Raw bytes or dictionary to compress.
        serialized:
            If True, treats ``q`` as pre-serialized bytes. If False, JSON-serializes
            before compression.

    Returns:
        URL-safe compressed string representation.

    Raises:
        TypeError: If ``q`` is not bytes or dict.
    """
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
    """Decodes and decompresses a URL-safe query payload.

    Reverses ``compress_query`` by restoring padding, base64 decoding, and Brotli
    decompressing. Optionally parses JSON into a dictionary.

    Args:
        q:
            URL-safe compressed string.
        serialized:
            If True, returns raw decompressed bytes. If False, parses decompressed JSON
            into a dict.

    Returns:
        Decompressed bytes or dictionary.

    Raises:
        TypeError:
            If ``q`` is not a string.
        ValueError:
            If decoding or decompression fails.
    """
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
