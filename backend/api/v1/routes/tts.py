"""Text-to-speech proxy — ElevenLabs voice for Buddy.

The ElevenLabs API key stays on the server. Buddy POSTs the King's reply text here and gets back
MP3 audio in a natural voice (default: "Rachel", a calm female voice). If this endpoint is
unavailable — no key configured, or a network/ElevenLabs error — the client falls back to the
device's built-in TTS, so Buddy always speaks.

Configure with environment variables (server-side only):
    ELEVENLABS_API_KEY    required to enable ElevenLabs
    ELEVENLABS_VOICE_ID   optional, default Indian female (2F1KINpxsttim2WfMbVs)
    ELEVENLABS_MODEL      optional, default eleven_multilingual_v2

Use GET /v1/voices/available to list the voices on your ElevenLabs account and copy the exact
voice_id you want, then set ELEVENLABS_VOICE_ID.
"""
from __future__ import annotations

import json
import os
import urllib.request

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.api.deps import get_principal

router = APIRouter(prefix="/v1", tags=["voice"])

# Default voice: Indian female (Hindi/English). Override with ELEVENLABS_VOICE_ID.
# NOTE: Voice-Library voices must be added to your ElevenLabs account first (and usually need a
# paid tier for API access). Use GET /v1/voices/available to pick one that's on your account.
_DEFAULT_VOICE = "2F1KINpxsttim2WfMbVs"
_URL = "https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128"
_VOICES_URL = "https://api.elevenlabs.io/v1/voices"


class TtsRequest(BaseModel):
    text: str


def _synthesize(text: str) -> bytes:
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise HTTPException(503, "voice not configured")
    vid = os.getenv("ELEVENLABS_VOICE_ID", _DEFAULT_VOICE)
    model = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    payload = json.dumps({
        "text": text[:2500],
        "model_id": model,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }).encode("utf-8")
    req = urllib.request.Request(
        _URL.format(vid=vid), data=payload, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


@router.post("/tts")
def tts(body: TtsRequest, principal=Depends(get_principal)):
    """Synthesize speech for the given text. Sync handler → runs in a threadpool."""
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text required")
    try:
        audio = _synthesize(text)
    except HTTPException:
        raise
    except Exception as exc:  # network / ElevenLabs error — client falls back to device TTS
        raise HTTPException(502, f"tts failed: {exc}")
    return Response(content=audio, media_type="audio/mpeg")


@router.get("/voices/available")
def voices_available(principal=Depends(get_principal)):
    """List the ElevenLabs voices on the configured account (id, name, labels) so an admin can
    pick the exact voice and set ELEVENLABS_VOICE_ID. Highlights the current default."""
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise HTTPException(503, "voice not configured")
    req = urllib.request.Request(_VOICES_URL, headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(502, f"could not list voices: {exc}")
    current = os.getenv("ELEVENLABS_VOICE_ID", _DEFAULT_VOICE)
    voices = [{
        "voice_id": v.get("voice_id"),
        "name": v.get("name"),
        "labels": v.get("labels", {}),
        "preview_url": v.get("preview_url"),
        "active": v.get("voice_id") == current,
    } for v in data.get("voices", [])]
    return {"count": len(voices), "current": current, "voices": voices}
