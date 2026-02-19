import secrets

from app.database.models.api_key import ApiKey, API_KEY_LENGTH
from app.utils import aware_utcnow


def generate_api_key() -> str:
    """Generate a cryptographically secure API key string.

    Returns:
        A securely generated API key string.
    """
    sequence = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(secrets.choice(sequence) for _ in range(API_KEY_LENGTH))


def validate_api_key(api_key: ApiKey) -> dict[str, int]:
    """Validate an API key and return a JWT-style payload.

    Args:
        api_key:
            Persisted API key model instance.

    Returns:
        A dictionary of the user ID, issued-at timestamp, and expiration timestamp.

    Raises:
        ValueError:
            If the key is missing, expired, or revoked.
    """
    if not api_key:
        raise ValueError("API key not found")

    if api_key.expires_at <= aware_utcnow():
        raise ValueError("API key has expired")

    if api_key.is_revoked:
        raise ValueError("API key is revoked")

    return {
        "sub": api_key.user_id,
        "iat": int(api_key.created_at.timestamp()),
        "exp": int(api_key.expires_at.timestamp())
    }
