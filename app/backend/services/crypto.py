import os
import base64
from cryptography.fernet import Fernet

_KEY = os.environ.get("SECRET_KEY", "")
_fernet = None


def _get_fernet() -> Fernet:
    global _fernet, _KEY
    if _fernet:
        return _fernet
    if not _KEY:
        # Generate a key at runtime if none set (dev mode)
        _KEY = Fernet.generate_key().decode()
    key_bytes = _KEY.encode() if isinstance(_KEY, str) else _KEY
    # Fernet requires a 32-byte url-safe base64 key
    if len(key_bytes) != 44:
        key_bytes = base64.urlsafe_b64encode(key_bytes[:32].ljust(32, b"0"))
    _fernet = Fernet(key_bytes)
    return _fernet


def encrypt(value: str) -> str:
    if not value:
        return value
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value:
        return value
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        return ""
