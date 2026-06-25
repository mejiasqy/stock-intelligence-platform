from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_intelligence"
    api_secret_key: str = "change-me-in-production"
    environment: str = "development"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_methods: list[str] = ["GET", "POST", "OPTIONS"]
    cors_allow_headers: list[str] = ["Content-Type", "X-Api-Key", "X-Request-ID"]

    # Pagination
    pagination_default_limit: int = 50
    pagination_max_limit: int = 100
    pagination_max_limit_trades: int = 500

    # Rate limits (requests/minute per IP, per instance — not distributed)
    rate_limit_default: str = "120/minute"
    rate_limit_rankings: str = "30/minute"
    rate_limit_analysis: str = "30/minute"
    rate_limit_admin: str = "20/minute"
    rate_limit_ingestion: str = "10/minute"
    rate_limit_backtests: str = "10/minute"


settings = Settings()
