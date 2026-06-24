import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    obsidian_vault_path: str = "./my_vault"
    llm_provider: str = "gemini"
    llm_model_name: str = "gemini-2.5-flash"
    llm_temperature: float = 0.2

    # API Keys
    gemini_api_key: str | None = None
    openai_api_key: str | None = None

    # Google Calendar
    gcal_credentials_path: str = "credentials.json"
    gcal_token_path: str = "token.json"
    gcal_calendar_id: str = "primary"


settings = Settings()

# Export API keys to environment variables so external LLM libraries can detect them
if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
