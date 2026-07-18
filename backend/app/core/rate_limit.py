import logging

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
        call_next,  # type: ignore[no-untyped-def]
    ) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        if request.url.path.startswith("/auth/"):
            return await call_next(request)

        identifier = self._get_identifier(request)
        key = f"rate_limit:{identifier}"
        window = settings.rate_limit_window_seconds

        try:
            count = await cache_service.increment(key, ttl=window)
        except Exception:
            logger.warning("Rate limit check failed, allowing request")
            return await call_next(request)

        limit = self._get_limit(request)

        if count > limit:
            return Response(
                content='{"success":false,"error":{"code":"RATE_LIMIT_EXCEEDED","message":"Rate limit exceeded"}}',
                status_code=429,
                media_type="application/json",
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response

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
