from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI
    mistral_api_key: str = ""

    # Integrations
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    google_pubsub_topic: str = ""

    # Calendly
    calendly_api_key: str = ""

    # Database
    database_url: str = ""

    # Security
    api_secret_key: str = ""  # HMAC signing key for internal webhooks
    encryption_key: str = ""  # Fernet key for content at rest
    allowed_webhook_ips: str = ""  # comma-separated IP allowlist e.g. "35.191.0.0/16"

    # App
    environment: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def webhook_ip_allowlist(self) -> list[str]:
        if not self.allowed_webhook_ips:
            return []
        return [ip.strip() for ip in self.allowed_webhook_ips.split(",")]


settings = Settings()
