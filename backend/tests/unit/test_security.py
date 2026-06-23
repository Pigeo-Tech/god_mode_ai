"""Tests for the Phase 9 security layer (JWT, passwords, auth)."""
from __future__ import annotations

import pytest

from backend.core.permission_manager.permissions import PermissionManager
from backend.security.auth_service import AuthError, AuthService
from backend.security.jwt_service import (ExpiredToken, InvalidToken, JwtService)
from backend.security.passwords import PasswordHasher


# --------------------------------------------------------------------------- jwt
def test_jwt_roundtrip_preserves_claims():
    jwt = JwtService("secret")
    token = jwt.issue("user-1", ["chat:write"])
    payload = jwt.verify(token)
    assert payload["sub"] == "user-1"
    assert payload["scopes"] == ["chat:write"]


def test_jwt_expired_rejected():
    jwt = JwtService("secret")
    token = jwt.issue("u", ttl=-1)
    with pytest.raises(ExpiredToken):
        jwt.verify(token)


def test_jwt_tampered_rejected():
    jwt = JwtService("secret")
    token = jwt.issue("u")
    tampered = token[:-2] + ("AB" if token[-2:] != "AB" else "CD")
    with pytest.raises(InvalidToken):
        jwt.verify(tampered)


def test_jwt_wrong_secret_rejected():
    token = JwtService("secret-a").issue("u")
    with pytest.raises(InvalidToken):
        JwtService("secret-b").verify(token)


# --------------------------------------------------------------------------- passwords
def test_password_hash_and_verify():
    h = PasswordHasher(iterations=10_000)  # fewer iters keeps the test fast
    stored = h.hash("hunter2")
    assert h.verify("hunter2", stored)
    assert not h.verify("wrong", stored)
    assert stored != h.hash("hunter2")  # salted -> different each time


# --------------------------------------------------------------------------- auth service
def _auth(with_perms=True):
    pm = PermissionManager() if with_perms else None
    if pm:
        pm.grant("user", "chat:write")
    return AuthService(JwtService("s"), PasswordHasher(iterations=10_000), permissions=pm), pm


def test_register_login_and_access():
    auth, pm = _auth()
    auth.register("a@example.com", "pw", roles=["user"])
    tokens = auth.authenticate("a@example.com", "pw")
    assert tokens["token_type"] == "bearer"
    principal = auth.verify_access(tokens["access_token"])
    assert "chat:write" in principal.scopes


def test_duplicate_registration_rejected():
    auth, _ = _auth()
    auth.register("a@example.com", "pw")
    with pytest.raises(AuthError):
        auth.register("a@example.com", "pw")


def test_bad_credentials_rejected():
    auth, _ = _auth()
    auth.register("a@example.com", "pw")
    with pytest.raises(AuthError):
        auth.authenticate("a@example.com", "nope")


def test_refresh_issues_access_but_refresh_not_accepted_as_access():
    auth, _ = _auth()
    auth.register("a@example.com", "pw", roles=["user"])
    tokens = auth.authenticate("a@example.com", "pw")
    refreshed = auth.refresh(tokens["refresh_token"])
    assert refreshed["token_type"] == "bearer"
    # a refresh token must not pass as an access token
    with pytest.raises(AuthError):
        auth.verify_access(tokens["refresh_token"])
