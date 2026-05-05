from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PORT: int = 8000
    SECRET_TOKEN: str = ""          # optional auth token
    CORS_ORIGINS: List[str] = ["*"]
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
