"""
Symmetric encryption for sensitive content stored in the database.
Uses Fernet (AES-128-CBC + HMAC-SHA256) — simple, audited, good enough.
Key must be 32 url-safe base64 bytes — generate with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import os

from cryptography.fernet import Fernet, InvalidToken

_DEV_KEY = Fernet.generate_key()  # stable within one process, dev only


def _get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY", "")
    if not key:
        return Fernet(_DEV_KEY)  # same key for encrypt+decrypt in dev/test
    return Fernet(key.encode())


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Decryption failed — invalid key or corrupted data") from e
