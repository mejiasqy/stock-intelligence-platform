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

    # LLM — nunca expor llm_api_key em logs, respostas HTTP ou OpenAPI
    llm_provider: str = "anthropic"
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_api_key: str = ""
    llm_timeout_seconds: int = 30
    llm_max_output_tokens: int = 1024

    # Alertas — nunca expor telegram_bot_token/telegram_chat_id
    alerts_enabled: bool = False
    alerts_dry_run: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    alert_on_signal_change: bool = True
    alert_score_high_threshold: float = 70.0
    alert_score_low_threshold: float = 25.0
    alert_dedup_hours: int = 24

    # Scheduler — inicia somente se scheduler_enabled=true
    scheduler_enabled: bool = False
    daily_job_time: str = "18:00"
    daily_job_timezone: str = "America/Sao_Paulo"


settings = Settings()
