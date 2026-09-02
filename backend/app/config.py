from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_local_env() -> None:
    """Load simple KEY=VALUE entries without overriding a real environment variable."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("AIPEDIA_DATABASE_URL", "sqlite:///./aipedia.db")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("AIPEDIA_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )
    agnes_api_key: str | None = os.getenv("AGNES_API_KEY")
    agnes_base_url: str = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip(
        "/"
    )
    agnes_model: str = os.getenv("AGNES_MODEL", "agnes-2.5-flash")


settings = Settings()
