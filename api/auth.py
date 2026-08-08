"""API authentication utilities for validating API keys and bearer tokens."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from connexion.lifecycle import ConnexionRequest

    from app.database import PostgresqlDB

from jwt.exceptions import ExpiredSignatureError, InvalidIssuerError, InvalidTokenError

from app.database.models import ApiKey
from app.security import hash_api_key, validate_api_key, validate_token


async def api_key_info(key: str, request: ConnexionRequest) -> dict[str, Any] | None:
    """Validate and return API key metadata.

    Args:
        key:
            API key string.
        request:
            Incoming request context.

    Returns:
    -------
        Token payload if valid, otherwise ``None``.
    """
    db: PostgresqlDB = request.state.db
    api_key = await db.get(ApiKey, hashed_key=hash_api_key(key))

    try:
        return validate_api_key(api_key)
    except ValueError:
        return None


async def bearer_info(token: str) -> dict[str, Any] | None:
    """Validate and decode a bearer JWT token.

    Args:
        token:
            Bearer token string.

    Returns:
    -------
        Decoded token payload if valid, otherwise ``None``.
    """
    try:
        return validate_token(token)
    except InvalidIssuerError, ExpiredSignatureError, InvalidTokenError:
        return None
