"""Hash de contraseñas, tokens JWT y cifrado de credenciales de las fuentes."""

import base64
import hashlib
import hmac
import os
from datetime import timedelta

import jwt
from cryptography.fernet import Fernet

from app.core import clock


class PasswordHasher:
    """PBKDF2-SHA256 con sal aleatoria (librería estándar de Python)."""

    def __init__(self, iterations: int = 200_000):
        self.iterations = iterations

    def hash(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.iterations)
        return "pbkdf2_sha256${}${}${}".format(
            self.iterations,
            base64.b64encode(salt).decode(),
            base64.b64encode(digest).decode(),
        )

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            _, iterations, salt_b64, digest_b64 = password_hash.split("$")
        except ValueError:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(digest, expected)


class TokenProvider:
    """Genera y valida tokens JWT (HS256)."""

    def __init__(self, secret: str, minutes: int = 60):
        self.secret = secret
        self.minutes = minutes

    def create_access_token(self, subject: int, role: str) -> str:
        payload = {
            "sub": str(subject),
            "role": role,
            "exp": clock.now() + timedelta(minutes=self.minutes),
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self.secret, algorithms=["HS256"])


class CredentialCipher:
    """Cifra la contraseña de conexión de cada fuente con Fernet (AES)."""

    def __init__(self, key: str | None = None):
        self._fernet = Fernet(key.encode() if key else Fernet.generate_key())

    def encrypt(self, plain: str) -> str:
        return self._fernet.encrypt(plain.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self._fernet.decrypt(token.encode()).decode()
