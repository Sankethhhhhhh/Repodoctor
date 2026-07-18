import logging
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.cache.service import cache_service
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in self.SKIP_PATHS:
            response: Response = await call_next(request)
            return response

        if request.url.path.startswith("/auth/"):
            auth_response: Response = await call_next(request)
            return auth_response

        identifier = self._get_identifier(request)
        key = f"rate_limit:{identifier}"
        window = settings.rate_limit_window_seconds

        try:
            count = await cache_service.increment(key, ttl=window)
        except Exception:
            logger.warning("Rate limit check failed, allowing request")
            fallback: Response = await call_next(request)
            return fallback

        limit = self._get_limit(request)

        if count > limit:
            rate_limited: Response = Response(
                content='{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"Rate limit exceeded"}}',
                status_code=429,
                media_type="application/json",
            )
            return rate_limited

        ok_response: Response = await call_next(request)
        ok_response.headers["X-RateLimit-Limit"] = str(limit)
        ok_response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return ok_response

    def _get_identifier(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else "unknown"
        return f"ip:{ip}"

    def _get_limit(self, request: Request) -> int:
        auth_header = request.headers.get("Authorization")
        cookie = request.cookies.get("session_token")
        if auth_header or cookie:
            return settings.rate_limit_authenticated
        return settings.rate_limit_anonymous
