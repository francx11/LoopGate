import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


def _default_projects_root() -> str:
    """Cross-platform default: ~/projects on POSIX, ~/Documents/Projects on Windows."""
    home = Path.home()
    if os.name == "nt":
        return str(home / "Documents" / "Projects")
    return str(home / "projects")


class Settings(BaseSettings):
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    SECRET_TOKEN: str = ""
    CORS_ORIGINS: List[str] = []
    LOG_LEVEL: str = "info"
    DEBUG: bool = False
    PROJECTS_ROOT: str = _default_projects_root()
    STORE_BACKEND: str = "memory"  # "memory" | "sqlite"
    SQLITE_PATH: str = "loopgate.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
