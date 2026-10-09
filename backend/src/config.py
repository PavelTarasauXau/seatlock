from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8" 
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    hold_expiration_interval_seconds: int = 30
    DATABASE_URL: str 
    google_client_id: str
    google_client_secret: SecretStr
    payment_webhook_secret: SecretStr
    enable_fake_provider: bool = True

settings = Settings()