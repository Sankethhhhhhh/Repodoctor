import logging
from datetime import UTC, datetime, timedelta

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_OAUTH_URL = "https://github.com/login/oauth"
GITHUB_API_URL = "https://api.github.com"


class GitHubTokenResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str


class GitHubUser(BaseModel):
    id: int
    login: str
    avatar_url: str | None
    name: str | None


class AuthService:
    def get_github_login_url(self, state: str) -> str:
        return (
            f"{GITHUB_OAUTH_URL}/authorize"
            f"?client_id={settings.github_client_id}"
            f"&redirect_uri={settings.github_callback_url}"
            f"&scope=read:user"
            f"&state={state}"
        )

    async def exchange_code(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_OAUTH_URL}/access_token",
                json={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_callback_url,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                logger.error("GitHub OAuth exchange failed: %d", response.status_code)
                raise ValueError("GitHub OAuth exchange failed")

            data = response.json()
            if "access_token" not in data:
                logger.error("GitHub OAuth response missing token")
                raise ValueError("GitHub OAuth response missing token")

            return data["access_token"]

    async def get_github_user(self, token: str) -> GitHubUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_URL}/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )

            if response.status_code != 200:
                raise ValueError("Failed to fetch GitHub user")

            data = response.json()
            return GitHubUser(
                id=data["id"],
                login=data["login"],
                avatar_url=data.get("avatar_url"),
                name=data.get("name"),
            )


class TokenPayload(BaseModel):
    user_id: str
    username: str
    exp: datetime


class TokenService:
    def create_token(
        self,
        user_id: str,
        username: str,
    ) -> str:
        import base64
        import hashlib
        import hmac
        import json

        payload = TokenPayload(
            user_id=user_id,
            username=username,
            exp=datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes),
        )

        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()

        body = base64.urlsafe_b64encode(payload.model_dump_json().encode()).rstrip(b"=").decode()

        signature = hmac.new(
            settings.secret_key.encode(),
            f"{header}.{body}".encode(),
            hashlib.sha256,
        ).digest()

        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

        return f"{header}.{body}.{sig_b64}"

    def verify_token(self, token: str) -> TokenPayload | None:
        import base64
        import hashlib
        import hmac
        import json

        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header, body, sig_b64 = parts

            expected_sig = hmac.new(
                settings.secret_key.encode(),
                f"{header}.{body}".encode(),
                hashlib.sha256,
            ).digest()

            padding = 4 - len(sig_b64) % 4
            sig_b64_padded = sig_b64 + "=" * padding
            actual_sig = base64.urlsafe_b64decode(sig_b64_padded)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            body_padded = body + "=" * (4 - len(body) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(body_padded))

            payload = TokenPayload(**payload_data)

            if payload.exp < datetime.now(UTC):
                return None

            return payload

        except Exception:
            logger.debug("Token verification failed")
            return None
