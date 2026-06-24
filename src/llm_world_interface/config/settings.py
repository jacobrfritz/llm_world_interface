from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    obsidian_vault_path: str = "./my_vault"
    llm_provider: str = "gemini"
    llm_model_name: str = "gemini-2.5-flash"
    llm_temperature: float = 0.2

    # Google Calendar
    gcal_credentials_path: str = "credentials.json"
    gcal_token_path: str = "token.json"
    gcal_calendar_id: str = "primary"


settings = Settings()
