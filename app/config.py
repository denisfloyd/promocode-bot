from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./promocode.db"
    admin_token: str = "change-me-to-a-secret-token"
    default_scrape_interval: int = 30
    cache_ttl: int = 300
    rate_limit: str = "60/minute"
    log_level: str = "INFO"

    # Telegram (optional — get from https://my.telegram.org)
    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_channels: str = ""  # Comma-separated channel usernames

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
