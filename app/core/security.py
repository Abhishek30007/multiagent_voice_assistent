import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import get_settings


def get_fernet_instance() -> Fernet:
    """Initialize a Fernet instance using the configured secret key.
    
    If the key is not already a valid 32-byte url-safe base64 string,
    derive one deterministically using SHA-256.
    """
    settings = get_settings()
    raw_key = settings.TOKEN_ENCRYPTION_KEY.strip()
    try:
        # Check if already a valid fernet key
        return Fernet(raw_key.encode())
    except Exception:
        # Deterministically derive 32-byte urlsafe base64 key
        derived_key = hashlib.sha256(raw_key.encode()).digest()
        urlsafe_key = base64.urlsafe_b64encode(derived_key)
        return Fernet(urlsafe_key)


def encrypt_token(plain_text: str | None) -> str | None:
    """Encrypt sensitive OAuth token before storing in PostgreSQL."""
    if not plain_text:
        return None
    fernet = get_fernet_instance()
    encrypted_bytes = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_token(cipher_text: str | None) -> str | None:
    """Decrypt sensitive OAuth token retrieved from PostgreSQL."""
    if not cipher_text:
        return None
    fernet = get_fernet_instance()
    try:
        decrypted_bytes = fernet.decrypt(cipher_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt stored token: {e}") from e
