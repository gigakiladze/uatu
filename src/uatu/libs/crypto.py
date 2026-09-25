import hashlib
from functools import cache

from cryptography.fernet import Fernet, InvalidToken

from uatu.libs.config import settings


@cache
def _cipher() -> Fernet:
    return Fernet(settings.encryption_key.get_secret_value().encode())


def encrypt(plaintext: str) -> str:
    return _cipher().encrypt(plaintext.encode()).decode()

def decrypt(ciphertext: str) -> str:
    try:
        return _cipher().decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("cannot decrypt: wrong ENCRYPTION_KEY or corrupted value") from e


def fingerprint(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()[:16]    