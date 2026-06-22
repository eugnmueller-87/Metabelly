from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI
    mistral_api_key: str = ""

    # Integrations
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # Gmail — shared OAuth2 app (one Google Cloud project, two inboxes)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Gmail account 1 — support@metabelly.com
    gmail_support_refresh_token: str = ""
    gmail_support_email: str = ""

    # Gmail account 2 — second branded address
    gmail_info_refresh_token: str = ""
    gmail_info_email: str = ""

    google_pubsub_topic: str = ""

    # Calendly
    calendly_api_key: str = ""

    # Database
    database_url: str = ""

    # Security
    api_secret_key: str = ""
    encryption_key: str = ""
    allowed_webhook_ips: str = ""

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

    def gmail_accounts(self) -> dict[str, dict[str, str]]:
        """Returns configured Gmail accounts keyed by email address."""
        accounts = {}
        if self.gmail_support_email and self.gmail_support_refresh_token:
            accounts[self.gmail_support_email] = {
                "refresh_token": self.gmail_support_refresh_token,
                "email": self.gmail_support_email,
            }
        if self.gmail_info_email and self.gmail_info_refresh_token:
            accounts[self.gmail_info_email] = {
                "refresh_token": self.gmail_info_refresh_token,
                "email": self.gmail_info_email,
            }
        return accounts


settings = Settings()
