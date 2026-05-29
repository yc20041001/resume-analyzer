"""Application configuration via environment variables."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM 配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Redis 配置（可选）
    REDIS_HOST: Optional[str] = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", "3600"))

    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # 阿里云 FC 兼容
    FC_ENABLED: bool = os.getenv("FC_ENABLED", "").lower() in ("1", "true", "yes")


settings = Settings()
