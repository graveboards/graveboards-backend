import secrets

from app.database.models.api_key import ApiKey, API_KEY_LENGTH
from app.utils import aware_utcnow


def generate_api_key() -> str:
    sequence = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(secrets.choice(sequence) for _ in range(API_KEY_LENGTH))


def validate_api_key(api_key: ApiKey) -> dict[str, int]:
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
