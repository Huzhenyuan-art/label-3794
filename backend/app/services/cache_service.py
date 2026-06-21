import hashlib
import json
import logging
from typing import Any

import redis

from ..config import Config

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self._client: redis.Redis | None = None
        self._enabled: bool = False

    def init_app(self, app) -> None:
        self._enabled = app.config.get("REDIS_CACHE_ENABLED", True)
        if not self._enabled:
            app.logger.info("Redis 缓存已禁用")
            return

        try:
            redis_kwargs = {
                "host": app.config["REDIS_HOST"],
                "port": app.config["REDIS_PORT"],
                "db": app.config["REDIS_DB"],
                "decode_responses": True,
                "socket_connect_timeout": 2,
                "socket_timeout": 2,
                "retry_on_timeout": True,
            }
            password = app.config.get("REDIS_PASSWORD")
            if password:
                redis_kwargs["password"] = password

            self._client = redis.Redis(**redis_kwargs)
            self._client.ping()
            app.logger.info(
                "Redis 缓存连接成功: %s:%s/%s",
                app.config["REDIS_HOST"],
                app.config["REDIS_PORT"],
                app.config["REDIS_DB"],
            )
        except Exception as exc:
            app.logger.warning("Redis 缓存连接失败，缓存将被跳过: %s", exc)
            self._client = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def _build_key(self, *parts: Any) -> str:
        return ":".join(str(p) for p in (Config.CACHE_KEY_PREFIX, *parts))

    def _hash_params(self, params: dict) -> str:
        serialized = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis GET 失败 key=%s: %s", key, exc)
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self.enabled:
            return
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            ex = ttl if ttl is not None else Config.REDIS_CACHE_TTL
            self._client.set(key, serialized, ex=ex)
        except Exception as exc:
            logger.warning("Redis SET 失败 key=%s: %s", key, exc)

    def delete(self, key: str) -> None:
        if not self.enabled:
            return
        try:
            self._client.delete(key)
        except Exception as exc:
            logger.warning("Redis DELETE 失败 key=%s: %s", key, exc)

    def delete_pattern(self, pattern: str) -> int:
        if not self.enabled:
            return 0
        try:
            keys = list(self._client.scan_iter(match=pattern, count=200))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as exc:
            logger.warning("Redis DELETE PATTERN 失败 pattern=%s: %s", pattern, exc)
            return 0

    def make_record_list_key(self, page_id: int, params: dict) -> str:
        return self._build_key(
            Config.CACHE_KEY_RECORD_LIST,
            page_id,
            self._hash_params(params),
        )

    def make_record_single_key(self, page_id: int, record_id: int) -> str:
        return self._build_key(
            Config.CACHE_KEY_RECORD_SINGLE,
            page_id,
            record_id,
        )

    def make_page_list_pattern(self, page_id: int) -> str:
        return self._build_key(Config.CACHE_KEY_RECORD_LIST, page_id, "*")

    def make_page_single_pattern(self, page_id: int) -> str:
        return self._build_key(Config.CACHE_KEY_RECORD_SINGLE, page_id, "*")

    def invalidate_page_cache(self, page_id: int) -> int:
        count = 0
        count += self.delete_pattern(self.make_page_list_pattern(page_id))
        count += self.delete_pattern(self.make_page_single_pattern(page_id))
        if count > 0:
            logger.info("已失效 page_id=%s 的 %s 个缓存键", page_id, count)
        return count


cache_service = CacheService()
