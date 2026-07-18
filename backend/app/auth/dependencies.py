from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import TokenPayload, TokenService
from app.core.database import get_db
from app.repositories.report_repo import UserRepository

token_service = TokenService()


async def get_current_user(
    access_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = token_service.verify_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return payload


async def get_optional_user(
    access_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload | None:
    if not access_token:
        return None

    payload = token_service.verify_token(access_token)
    if not payload:
        return None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        return None

    return payload
