"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-side configuration. Never expose these values to clients."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    rate_limit_per_minute: int = Field(default=20, alias="RATE_LIMIT_PER_MINUTE")
    allowed_origins: str = Field(
        default="http://localhost:8000", alias="ALLOWED_ORIGINS"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse the comma-separated ``allowed_origins`` string into a clean list."""
        origins = self.allowed_origins.split(",")  # pylint: disable=no-member
        return [origin.strip() for origin in origins if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, loaded once per process."""
    return Settings()
