"""System routes — health, readiness, metrics (unauthenticated, for probes/scrapers)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from backend.api.deps import get_service

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    return {"status": "ok", "phase": 9}


@router.get("/health/ready")
async def ready(response: Response, service=Depends(get_service)):
    code, detail = await service.health()
    response.status_code = code
    return detail


@router.get("/metrics")
async def metrics(service=Depends(get_service)):
    return Response(content=service.metrics(), media_type="text/plain")
