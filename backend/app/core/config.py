from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_intelligence"
    api_secret_key: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"


settings = Settings()
