"""FastAPI dependencies — service access and auth.

Phase 9. Resolves the ApiService / AuthService from app state and authenticates the bearer token
into a Principal, with an optional scope guard for RBAC-protected routes.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status

from backend.security.auth_service import AuthError, Principal


def get_service(request: Request):
    return request.app.state.service


def get_auth(request: Request):
    return request.app.state.auth


async def get_principal(request: Request,
                        authorization: str | None = Header(default=None)) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        return request.app.state.auth.verify_access(token)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))


def require_scope(scope: str):
    async def guard(principal: Principal = Depends(get_principal)) -> Principal:
        granted = principal.scopes
        ok = "*" in granted or scope in granted or any(
            g.endswith(":*") and scope.startswith(g[:-1]) for g in granted)
        if not ok:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"missing scope {scope}")
        return principal
    return guard
