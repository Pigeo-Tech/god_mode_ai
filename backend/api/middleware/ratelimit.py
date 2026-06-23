"""Per-client rate-limit middleware (token bucket).

Phase 9. Limits requests per client (by bearer token if present, else client IP) using the same
TokenBucketRateLimiter as the Tool Registry. Returns 429 when the bucket is empty.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.tool_registry.registry import RateLimitExceeded
from backend.tools.rate_limit import TokenBucketRateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, capacity: float = 120, refill_per_sec: float = 2.0) -> None:
        super().__init__(app)
        self._limiter = TokenBucketRateLimiter(capacity, refill_per_sec)

    def _client_key(self, request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if auth:
            return f"tok:{auth[-16:]}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    async def dispatch(self, request: Request, call_next):
        try:
            self._limiter.check(self._client_key(request))
        except RateLimitExceeded:
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        return await call_next(request)
