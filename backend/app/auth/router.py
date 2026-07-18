import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, token_service
from app.auth.service import AuthService, TokenPayload
from app.core.database import get_db
from app.repositories.report_repo import UserRepository

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@auth_router.get("/github/login")
async def github_login() -> Response:
    state = secrets.token_urlsafe(32)
    url = auth_service.get_github_login_url(state)
    return Response(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": url},
    )


@auth_router.get("/github/callback")
async def github_callback(
    code: str,
    _state: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        github_token = await auth_service.exchange_code(code)
        github_user = await auth_service.get_github_user(github_token)
    except ValueError as e:
        logger.error("GitHub OAuth failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub authentication failed",
        ) from e

    user_repo = UserRepository(db)
    user = await user_repo.get_or_create(
        github_id=github_user.id,
        username=github_user.login,
        avatar_url=github_user.avatar_url,
    )

    token = token_service.create_token(user.id, user.username)

    response = Response(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": "/"},
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings_cookie_max_age(),
    )
    return response


def settings_cookie_max_age() -> int:
    from app.config import settings

    return settings.access_token_expire_minutes * 60


@auth_router.get("/me")
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "user_id": current_user.user_id,
            "username": current_user.username,
        },
    }


@auth_router.post("/logout")
async def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(key="access_token")
    return response
