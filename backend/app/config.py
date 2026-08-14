"""Env-driven configuration (ticket 07: all host-specific values are env)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    auth_mode: str = "dev"  # google | dev
    dev_auth_token: str = ""  # enables the dev-login bypass when set
    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = "dev-only-change-me"
    app_base_url: str = "http://127.0.0.1:3000"
    web_port: int = 3000
    data_dir: str = "/data"

    @property
    def secure_cookies(self) -> bool:
        return self.app_base_url.startswith("https://")

    @property
    def session_days(self) -> int:
        return 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


def seed_defaults(settings: Settings | None = None) -> dict:
    """Non-secret defaults from config.yaml that pre-fill the account-creation
    form (ticket 07). Never holds secrets."""
    settings = settings or get_settings()
    defaults = {"currency": "MXN", "tax_percent": 2, "bank_fixed_fee": 320, "conv_percent": 0}
    path = Path(settings.data_dir) / "config.yaml"
    try:
        if path.exists():
            text = path.read_text()
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, _, value = line.partition(":")
                key, value = key.strip(), value.strip()
                if key == "currency":
                    defaults["currency"] = value
                elif key == "tax_percent":
                    defaults["tax_percent"] = float(value)
                elif key == "bank_fixed_fee":
                    defaults["bank_fixed_fee"] = float(value)
                elif key == "conv_percent":
                    defaults["conv_percent"] = float(value)
    except OSError:
        pass
    return defaults
