from connexion.lifecycle import ConnexionRequest
from jwt.exceptions import InvalidIssuerError, ExpiredSignatureError, InvalidTokenError

from app.database import PostgresqlDB
from app.database.models import ApiKey
from app.security import validate_api_key, validate_token


async def api_key_info(key: str, request: ConnexionRequest) -> dict | None:
    """Validate and return API key metadata.

    Args:
        key:
            API key string.
        request:
            Incoming request context.

    Returns:
        Token payload if valid, otherwise None.
    """
    db: PostgresqlDB = request.state.db
    api_key = await db.get(ApiKey, key=key)

    try:
        return validate_api_key(api_key)
    except ValueError:
        return None


async def bearer_info(token: str) -> dict | None:
    """Validate and decode a bearer JWT token.

    Returns:
        Decoded token payload if valid, otherwise ``None``.
    """
    try:
        return validate_token(token)
    except (InvalidIssuerError, ExpiredSignatureError, InvalidTokenError):
        return None
