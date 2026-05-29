"""Redis cache with graceful degradation.

If Redis is unavailable or not configured, falls back to an in-memory dict.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class ResumeCache:
    """Abstract cache — uses Redis when available, otherwise in-memory."""

    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None
        self._memory: dict[str, tuple[float, bytes]] = {}
        self._available = False
        self._init_redis()

    def _init_redis(self) -> None:
        if not settings.REDIS_HOST:
            logger.info("REDIS_HOST not set — using in-memory cache")
            return
        try:
            self._redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=False,
            )
            self._available = True
            logger.info("Redis cache initialized at %s:%s", settings.REDIS_HOST, settings.REDIS_PORT)
        except Exception as exc:
            logger.warning("Redis init failed, using in-memory cache: %s", exc)
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def _make_key(self, prefix: str, data: str) -> str:
        return f"{prefix}:{hashlib.md5(data.encode()).hexdigest()}"

    async def get(self, prefix: str, raw: str) -> Optional[Any]:
        key = self._make_key(prefix, raw)
        if self._available and self._redis:
            try:
                val = await self._redis.get(key)
                if val:
                    return json.loads(val)
            except Exception as exc:
                logger.warning("Redis get failed, falling back: %s", exc)
        # In-memory fallback
        entry = self._memory.get(key)
        if entry:
            expires, data = entry
            if time.time() < expires:
                return json.loads(data)
            del self._memory[key]
        return None

    async def set(self, prefix: str, raw: str, value: Any, ttl: Optional[int] = None) -> None:
        key = self._make_key(prefix, raw)
        data = json.dumps(value, ensure_ascii=False).encode()
        ttl = ttl or settings.REDIS_TTL
        if self._available and self._redis:
            try:
                await self._redis.setex(key, ttl, data)
                return
            except Exception as exc:
                logger.warning("Redis set failed, falling back: %s", exc)
        self._memory[key] = (time.time() + ttl, data)


# Singleton
cache = ResumeCache()
