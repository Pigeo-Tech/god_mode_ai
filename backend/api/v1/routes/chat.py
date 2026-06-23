"""Chat routes — submit an objective to the King and look up request status."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json

from backend.api.deps import get_principal, get_service
from backend.security.auth_service import Principal
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


@router.post("/chat")
async def chat(body: ChatRequest, principal: Principal = Depends(get_principal),
               service=Depends(get_service)):
    if body.stream:
        async def event_stream():
            async for event in service.stream_chat(body.message, principal.id):
                yield f"data: {json.dumps(event)}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    return await service.chat(body.message, principal.id)


@router.get("/requests/{request_id}")
async def get_request(request_id: str, principal: Principal = Depends(get_principal),
                      service=Depends(get_service)):
    found = service.get_request(request_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
    return found
