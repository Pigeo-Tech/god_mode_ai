"""FastAPI application entrypoint.

Phase 9. Builds the app, wires middleware (correlation id + rate limiting), mounts the v1 routers
and the WebSocket stream, and on startup brings up the whole agent platform (King + Generals +
Soldiers) plus the auth service. REST + WebSockets + streaming + JWT auth + OpenAPI.

Run (where dependencies are installed):
    uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.deps import get_principal, require_scope  # noqa: F401 (re-exported for routes)
from backend.api.middleware.correlation import CorrelationIdMiddleware
from backend.api.middleware.ratelimit import RateLimitMiddleware
from backend.api.service import ApiService
from backend.api.v1.routes import agents as agents_routes
from backend.api.v1.routes import auth as auth_routes
from backend.api.v1.routes import chat as chat_routes
from backend.api.v1.routes import system as system_routes
from backend.api.v1.websockets import stream as stream_ws
from backend.config.settings import settings
from backend.security.auth_service import AuthService
from backend.security.jwt_service import JwtService
from backend.security.passwords import PasswordHasher


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bring the agent platform online.
    service = await ApiService.create()
    jwt = JwtService(settings.jwt_secret, settings.jwt_algorithm,
                     ttl_seconds=settings.access_token_expire_minutes * 60)
    auth = AuthService(jwt, PasswordHasher(), permissions=service.container.permissions)
    app.state.service = service
    app.state.auth = auth
    yield
    await service.container.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="GOD MODE AI", version="0.9.0", lifespan=lifespan)
    # CORS so the web Admin dashboard (browser) can call the API. Bearer-token auth, no cookies.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    for module in (system_routes, auth_routes, chat_routes, agents_routes):
        app.include_router(module.router)
    app.include_router(stream_ws.router)
    return app


app = create_app()
