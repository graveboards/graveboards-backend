from cryptography.fernet import Fernet
from app.config import JWT_SECRET_KEY
import hashlib
import base64

_fernet_key = base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET_KEY.encode()).digest())
_fernet = Fernet(_fernet_key)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a token string using Fernet."""
    return _fernet.encrypt(plaintext.encode())


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt a Fernet-encrypted token string."""
    return _fernet.decrypt(ciphertext).decode()
