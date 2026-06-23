"""Built-in soldier tools (generated). Each non-custom soldier wraps one mock tool.

Deterministic, offline, structured output — swap any mock for a real provider behind the same
Tool Registry interface without touching callers.
"""
from __future__ import annotations

import hashlib

from backend.core.tool_registry.registry import FunctionTool, ToolRegistry


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def _weather(a):
    s = _seed(a.get("objective", ""))
    return {"location": a.get("objective", "unknown"), "temp_c": s % 35,
            "condition": ["sunny", "cloudy", "rainy", "windy"][s % 4]}


def _stock(a):
    s = _seed(a.get("objective", ""))
    return {"query": a.get("objective"), "price_usd": round(10 + s % 1000 + (s % 100) / 100, 2)}


def _crypto(a):
    s = _seed(a.get("objective", ""))
    return {"query": a.get("objective"), "price_usd": round(s % 70000 + (s % 100) / 100, 2)}


def _search(a):
    q = a.get("objective", "")
    return {"query": q, "results": [{"title": f"Result {i} for {q}"} for i in range(1, 4)]}


def _command(a):
    return {"command": a.get("objective", ""), "exit_code": 0, "stdout": "ok"}


SHAPERS = {
    "weather": _weather, "stock": _stock, "crypto": _crypto,
    "search": _search, "internet": _search, "research": _search, "news": _search,
    "terminal": _command, "git": _command, "docker": _command, "aws": _command,
    "kubernetes": _command, "database": _command,
}

TOOL_NAMES = ["internet", "search", "research", "news", "weather", "maps", "translation", "knowledge_graph", "calendar", "reminder", "task_planning", "project_planning", "route_planning", "goal_planning", "tool", "api", "terminal", "workflow", "automation", "short_term_memory", "semantic_memory", "context", "file", "ocr", "pdf", "vector_memory", "coding", "debugging", "git", "docker", "testing", "deployment", "image", "video", "audio", "music", "speech", "vision", "camera", "editing", "banking", "loan", "credit_card", "investment", "stock", "crypto", "shopping", "budget", "email", "whatsapp", "sms", "call", "notification", "contacts", "social_media", "aws", "azure", "gcp", "database", "kubernetes", "authentication", "monitoring", "logging", "devops", "trigger", "scheduler", "auto_workflow", "api_automation", "notification_automation", "device_control", "app_management", "settings", "flashlight", "volume", "brightness", "battery", "storage", "file_manager", "clipboard", "dev_camera", "gallery", "phone", "dev_contacts", "bluetooth", "wifi", "nfc", "sensor", "accessibility", "device_health", "malware", "antivirus", "threat_detection", "phishing", "scam_detection", "network_security", "firewall", "encryption", "password", "privacy", "secure_vault", "identity_protection", "incident_response", "smart_home", "smart_lighting", "smart_camera", "smart_tv", "smart_speaker", "appliance", "vehicle", "wearable", "medical_iot", "industrial_iot", "energy_management", "matter_protocol", "intelligence", "reasoning", "planning_optimization", "performance", "memory_optimization", "cpu_optimization", "gpu_optimization", "battery_optimization", "storage_optimization", "cache_optimization", "thermal_management", "prediction", "learning", "decision", "knowledge_evolution", "ai_model_selection", "resource_allocation", "self_diagnostics", "wake_word", "speech_recognition", "speaker_recognition", "voice_biometrics", "text_to_speech", "noise_cancellation", "emotion_detection", "language_understanding", "accent_adaptation", "offline_voice", "call_assistant", "conversation"]


def _make_fn(name: str):
    shaper = SHAPERS.get(name)

    async def fn(args: dict) -> dict:
        data = shaper(args) if shaper else {"summary": f"{name} handled: {args.get('objective', '')}"}
        return {"tool": name, "objective": args.get("objective", ""), "status": "ok", "data": data}

    return fn


def register_soldier_tools(registry: ToolRegistry) -> list[str]:
    for name in TOOL_NAMES:
        registry.register(FunctionTool(name, _make_fn(name)))
    return list(TOOL_NAMES)
