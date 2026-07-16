from cryptography.fernet import Fernet
from app.config import JWT_SECRET_KEY
import hashlib


def _get_fernet() -> Fernet:
    """Get a Fernet instance derived from the JWT secret key.

    The JWT secret is used as the basis for a deterministic Fernet key.
    This ensures all instances of the app use the same encryption key
    (as long as JWT_SECRET_KEY is unchanged).
    """
    key = hashlib.sha256(JWT_SECRET_KEY.encode()).digest()
    return Fernet(key)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a token string using Fernet."""
    return _get_fernet().encrypt(plaintext.encode())


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt a Fernet-encrypted token string."""
    return _get_fernet().decrypt(ciphertext).decode()
