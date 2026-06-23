"""Agents & tools introspection routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import get_principal, get_service

router = APIRouter(prefix="/v1", tags=["introspection"])


@router.get("/agents")
async def list_agents(principal=Depends(get_principal), service=Depends(get_service)):
    return service.list_agents()


@router.get("/tools")
async def list_tools(principal=Depends(get_principal), service=Depends(get_service)):
    return service.list_tools()
