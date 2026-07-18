from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.dependencies import token_service
from app.auth.service import AuthService, TokenService


class TestAuthService:
    def test_login_url_contains_client_id(self) -> None:
        service = AuthService()
        url = service.get_github_login_url("test_state")
        assert "client_id=" in url
        assert "state=test_state" in url
        assert "redirect_uri=" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self) -> None:
        service = AuthService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "gho_test_token",
            "token_type": "bearer",
            "scope": "read:user",
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            token = await service.exchange_code("test_code")
            assert token == "gho_test_token"

    @pytest.mark.asyncio
    async def test_exchange_code_failure(self) -> None:
        service = AuthService()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "bad_code"}

        with (
            patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response),
            pytest.raises(ValueError, match="GitHub OAuth exchange failed"),
        ):
            await service.exchange_code("bad_code")


class TestTokenService:
    def test_create_and_verify_token(self) -> None:
        service = TokenService()
        token = service.create_token("user-123", "testuser")
        payload = service.verify_token(token)
        assert payload is not None
        assert payload.user_id == "user-123"
        assert payload.username == "testuser"

    def test_verify_invalid_token(self) -> None:
        service = TokenService()
        payload = service.verify_token("invalid.token.here")
        assert payload is None

    def test_verify_tampered_token(self) -> None:
        service = TokenService()
        token = service.create_token("user-123", "testuser")
        parts = token.split(".")
        parts[1] = parts[1][::-1]
        tampered = ".".join(parts)
        payload = service.verify_token(tampered)
        assert payload is None

    def test_verify_empty_token(self) -> None:
        service = TokenService()
        payload = service.verify_token("")
        assert payload is None

    def test_token_payload_has_user_info(self) -> None:
        service = TokenService()
        token = service.create_token("user-456", "alice")
        payload = service.verify_token(token)
        assert payload is not None
        assert payload.user_id == "user-456"
        assert payload.username == "alice"
        assert payload.exp is not None


class TestTokenDependencies:
    def test_token_service_singleton(self) -> None:
        assert token_service is not None
        assert isinstance(token_service, TokenService)
