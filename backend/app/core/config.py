import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    secure_cookie: bool = False
    rate_limit_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "forbid"}


settings = Settings()

if settings.secret_key == "dev-secret-key-change-in-production":
    logger.warning(
        "SECRET_KEY is set to the default value. "
        "Change it in production via environment variable or .env file."
    )
