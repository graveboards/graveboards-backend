from datetime import timedelta
from typing import Any

import jwt

from app.utils import aware_utcnow
from app.config import FRONTEND_BASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM

JWT_LIFETIME_DAYS = 30


def generate_token(user_id: int | str) -> str:
    """Generate a signed JWT for the given user ID.

    Args:
        user_id:
            Identifier of the authenticated user.

    Returns:
        Encoded JWT string.
    """
    return encode_token(create_token_payload(user_id))


def create_token_payload(user_id: int | str) -> dict[str, Any]:
    """Create a JWT payload for authentication.

    Includes standard claims:
        - ``sub``: Subject (user ID)
        - ``iss``: Issuer (frontend base URL)
        - ``iat``: Issued-at timestamp
        - ``exp``: Expiration timestamp

    Args:
        user_id:
            Identifier of the authenticated user.

    Returns:
        JWT payload dictionary.
    """
    return {
        "sub": str(user_id),
        "iss": FRONTEND_BASE_URL,
        "iat": int(aware_utcnow().timestamp()),
        "exp": int((aware_utcnow() + timedelta(days=JWT_LIFETIME_DAYS)).timestamp())
    }


def encode_token(payload: dict[str, Any]) -> str:
    """Encode and sign a JWT payload.

    Args:
        payload:
            Token payload dictionary.

    Returns:
        Signed JWT string.
    """
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT.

    Args:
        token:
            Encoded JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        jwt.InvalidTokenError:
            If signature or structure is invalid.
        jwt.ExpiredSignatureError:
            If token has expired.
    """
    return jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def validate_token(token: str) -> dict[str, int]:
    """Validate a JWT and normalize its payload.

    Verifies:
        - Signature validity
        - Issuer matches expected frontend URL
        - Subject is convertible to an integer

    Args:
        token:
            Encoded JWT string.

    Returns:
        Normalized payload dictionary with ``sub`` as int.

    Raises:
        jwt.ExpiredSignatureError:
            If token is expired.
        jwt.InvalidTokenError:
            If validation fails.
    """
    try:
        payload = decode_token(token)
        sub = payload["sub"]

        if payload["iss"] != FRONTEND_BASE_URL:
            raise jwt.InvalidIssuerError("Invalid token issuer")

        if not sub.isdigit():
            raise jwt.InvalidTokenError("Subject is not convertable to an integer")

        payload["sub"] = int(sub)

        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise
