"""JWT service — HS256, implemented on the standard library.

Phase 9. A dependency-free HS256 JWT (encode/verify/exp) so auth runs and is testable offline.
The public surface matches what python-jose/PyJWT would offer, so swapping in a full library
later (for RS256, JWKS, etc.) is contained to this file.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


class TokenError(Exception):
    pass


class InvalidToken(TokenError):
    pass


class ExpiredToken(TokenError):
    pass


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


class JwtService:
    def __init__(self, secret: str, algorithm: str = "HS256", ttl_seconds: int = 1800) -> None:
        if algorithm != "HS256":
            raise ValueError("this stdlib implementation supports HS256 only")
        self._secret = secret.encode("utf-8")
        self._ttl = ttl_seconds

    def _sign(self, signing_input: bytes) -> str:
        return _b64url_encode(hmac.new(self._secret, signing_input, hashlib.sha256).digest())

    def issue(self, sub: str, scopes: list[str] | None = None,
              ttl: int | None = None, typ: str = "access") -> str:
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": sub, "scopes": scopes or [], "iat": now,
                   "exp": now + (ttl if ttl is not None else self._ttl), "token_type": typ}
        seg = f"{_b64url_encode(json.dumps(header).encode())}." \
              f"{_b64url_encode(json.dumps(payload).encode())}"
        return f"{seg}.{self._sign(seg.encode())}"

    def verify(self, token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            raise InvalidToken("malformed token")
        signing_input = f"{parts[0]}.{parts[1]}".encode()
        if not hmac.compare_digest(self._sign(signing_input), parts[2]):
            raise InvalidToken("bad signature")
        try:
            payload = json.loads(_b64url_decode(parts[1]))
        except Exception as exc:  # noqa: BLE001
            raise InvalidToken("bad payload") from exc
        if int(payload.get("exp", 0)) < time.time():
            raise ExpiredToken("token expired")
        return payload
