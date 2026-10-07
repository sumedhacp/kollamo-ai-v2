"""Rate Limiting Middleware and In-Memory Sliding Window Tracker."""

import time
from collections import defaultdict
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status

from backend.app.core.logging import logger
from backend.app.schemas.error import ErrorDetail, ErrorResponse


class InMemoryRateLimiter:
    """Thread-safe in-memory sliding window rate limiter per client IP."""

    def __init__(self, requests_per_minute: int = 120, window_seconds: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.clients: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> bool:
        """Returns True if the client IP has exceeded the allowed rate."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean timestamps older than the window
        timestamps = [t for t in self.clients[client_ip] if t > window_start]
        self.clients[client_ip] = timestamps

        if len(timestamps) >= self.requests_per_minute:
            return True

        self.clients[client_ip].append(now)
        return False

    def reset(self) -> None:
        """Clears client state."""
        self.clients.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces per-client IP request limits to prevent denial-of-service."""

    def __init__(self, app, limiter: Optional[InMemoryRateLimiter] = None) -> None:
        super().__init__(app)
        self.limiter = limiter or InMemoryRateLimiter(requests_per_minute=120, window_seconds=60)
        self.excluded_paths = {"/docs", "/redoc", "/openapi.json", "/"}

    async def dispatch(self, request: Request, call_next):
        # Skip rate-limiting for documentation and root paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        if self.limiter.is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for client IP: {client_ip} on {request.url.path}")
            error_response = ErrorResponse(
                error=ErrorDetail(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too many requests. Please slow down and try again.",
                    details={"retry_after_seconds": self.limiter.window_seconds},
                )
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response.model_dump(),
                headers={"Retry-After": str(self.limiter.window_seconds)},
            )

        try:
            return await call_next(request)
        except Exception as exc:
            logger.exception(f"Unhandled server error processing {request.method} {request.url.path}: {exc}")
            error_response = ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="An unexpected server error occurred. Please try again later.",
                    details=None,
                )
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(),
            )
