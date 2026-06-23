"""Password hashing — PBKDF2-HMAC-SHA256 (standard library).

Phase 9. Salted, iterated hashing with a constant-time verify. Format: ``pbkdf2$<iters>$<salt>$<hash>``
(both salt and hash hex-encoded). In production this can be swapped for argon2/bcrypt behind the
same interface.
"""
from __future__ import annotations

import hashlib
import hmac
import os

_ITERATIONS = 200_000


class PasswordHasher:
    def __init__(self, iterations: int = _ITERATIONS) -> None:
        self._iterations = iterations

    def hash(self, password: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self._iterations)
        return f"pbkdf2${self._iterations}${salt.hex()}${dk.hex()}"

    def verify(self, password: str, stored: str) -> bool:
        try:
            scheme, iters, salt_hex, hash_hex = stored.split("$")
            assert scheme == "pbkdf2"
            dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                     bytes.fromhex(salt_hex), int(iters))
        except Exception:  # noqa: BLE001
            return False
        return hmac.compare_digest(dk.hex(), hash_hex)
