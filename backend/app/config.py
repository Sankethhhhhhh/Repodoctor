from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "APP_", "env_file": ".env"}

    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./repodoctor.db"
    redis_url: str = "redis://localhost:6379/0"

    github_client_id: str = ""
    github_client_secret: str = ""
    github_token: str = ""
    github_callback_url: str = "http://localhost:8000/auth/github/callback"

    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    rate_limit_anonymous: int = 10
    rate_limit_authenticated: int = 100
    rate_limit_window_seconds: int = 3600

    webhook_secret: str = ""

    github_app_id: str = ""
    github_app_private_key: str = ""
    github_app_webhook_secret: str = ""

    ai_provider: str = "none"
    ai_model: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""


settings = Settings()
