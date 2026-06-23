"""Auth routes — register, login, refresh."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from backend.api.deps import get_auth
from backend.security.auth_service import AuthError

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, auth=Depends(get_auth)):
    try:
        user_id = auth.register(body.email, body.password)
    except AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    return {"user_id": user_id}


@router.post("/login")
async def login(body: LoginRequest, auth=Depends(get_auth)):
    try:
        return auth.authenticate(body.email, body.password)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))


@router.post("/refresh")
async def refresh(body: RefreshRequest, auth=Depends(get_auth)):
    try:
        return auth.refresh(body.refresh_token)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))
