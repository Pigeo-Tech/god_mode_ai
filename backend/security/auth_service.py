"""AuthService — registration, login, refresh, and token verification.

Phase 9. Ties the JWT service, password hasher, and (optionally) the Permission Manager together
behind a small API the routers call. Users are kept in an in-memory store here; a real
UserRepository (PostgreSQL) implements the same shape in production.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from uuid import uuid4

from backend.security.jwt_service import JwtService, TokenError


class AuthError(Exception):
    pass


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    roles: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_login: float | None = None


@dataclass
class Principal:
    id: str
    scopes: list[str]


class AuthService:
    def __init__(self, jwt: JwtService, hasher, permissions=None) -> None:
        self._jwt = jwt
        self._hasher = hasher
        self._permissions = permissions
        self._users: dict[str, User] = {}          # email -> User
        self._refresh_ttl = 7 * 24 * 3600

    def register(self, email: str, password: str, roles: list[str] | None = None) -> str:
        if email in self._users:
            raise AuthError("email already registered")
        user = User(id=str(uuid4()), email=email,
                    password_hash=self._hasher.hash(password), roles=roles or ["user"])
        self._users[email] = user
        if self._permissions is not None:
            for role in user.roles:
                self._permissions.assign(user.id, role)
        return user.id

    def _scopes_for(self, user: User) -> list[str]:
        if self._permissions is not None:
            return sorted(self._permissions.scopes_for(user.id))
        return [f"role:{r}" for r in user.roles]

    def list_users(self) -> list[dict]:
        """Admin view of registered users (no secrets)."""
        return [
            {"id": u.id, "email": u.email, "roles": list(u.roles),
             "scopes": self._scopes_for(u),
             "created_at": u.created_at, "last_login": u.last_login}
            for u in self._users.values()
        ]

    def authenticate(self, email: str, password: str) -> dict:
        user = self._users.get(email)
        if user is None or not self._hasher.verify(password, user.password_hash):
            raise AuthError("invalid credentials")
        user.last_login = time.time()
        scopes = self._scopes_for(user)
        return {
            "access_token": self._jwt.issue(user.id, scopes, typ="access"),
            "refresh_token": self._jwt.issue(user.id, scopes, ttl=self._refresh_ttl,
                                             typ="refresh"),
            "token_type": "bearer",
            "user_id": user.id,
        }

    def refresh(self, refresh_token: str) -> dict:
        payload = self._verify(refresh_token)
        if payload.get("token_type") != "refresh":
            raise AuthError("not a refresh token")
        return {"access_token": self._jwt.issue(payload["sub"], payload.get("scopes", []),
                                                typ="access"), "token_type": "bearer"}

    def verify_access(self, token: str) -> Principal:
        payload = self._verify(token)
        if payload.get("token_type") != "access":
            raise AuthError("not an access token")
        return Principal(id=payload["sub"], scopes=payload.get("scopes", []))

    def _verify(self, token: str) -> dict:
        try:
            return self._jwt.verify(token)
        except TokenError as exc:
            raise AuthError(str(exc)) from exc
