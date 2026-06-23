"""WebSocket streaming — live King progress for an objective.

Phase 9. Client connects, sends ``{"token": "...", "message": "..."}``; the server authenticates,
streams lifecycle/progress/result events, then closes.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.security.auth_service import AuthError

router = APIRouter()


@router.websocket("/v1/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    auth = ws.app.state.auth
    service = ws.app.state.service
    try:
        payload = await ws.receive_json()
        token = payload.get("token", "")
        try:
            principal = auth.verify_access(token)
        except AuthError as exc:
            await ws.send_json({"type": "error", "error": str(exc)})
            await ws.close(code=4401)
            return

        message = payload.get("message", "")
        async for event in service.stream_chat(message, principal.id):
            await ws.send_json(event)
        await ws.close()
    except WebSocketDisconnect:
        return
