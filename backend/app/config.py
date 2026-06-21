import os
from datetime import timedelta
from urllib.parse import quote_plus


class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    SECRET_KEY = os.getenv(
        "APP_SECRET_KEY", "dev_app_secret_key_please_change_this_to_random_32_chars"
    )
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "dev_jwt_secret_key_please_change_this_to_random_32_chars"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
    DB_NAME = os.getenv("DB_NAME", "label_portal")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4&connect_timeout=10&read_timeout=30&write_timeout=30"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_use_lifo": True,
        "connect_args": {
            "connect_timeout": 10,
            "read_timeout": 30,
            "write_timeout": 30,
        },
        "execution_options": {
            "isolation_level": "READ COMMITTED",
        },
    }

    DB_QUERY_TIMEOUT = int(os.getenv("DB_QUERY_TIMEOUT", "30"))
    DB_STATEMENT_TIMEOUT = int(os.getenv("DB_STATEMENT_TIMEOUT", "60"))

    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "Q8mCU8FlS8aM2O7uTvN9L0n8I4n7hDq8k1P7qQ6Kf-I=")

    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
    CAPTCHA_REQUIRED_THRESHOLD = int(os.getenv("CAPTCHA_REQUIRED_THRESHOLD", "2"))

    UPLOAD_ROOT = os.path.join(BASE_DIR, "static", "pages")

    DEFAULT_ALLOWED_EXTENSIONS = [
        "html",
        "htm",
        "php",
        "css",
        "js",
        "json",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "svg",
        "ico",
        "webp",
        "txt",
        "zip",
    ]
    BLOCKED_EXTENSIONS = [
        "exe",
        "msi",
        "bat",
        "cmd",
        "com",
        "dll",
        "so",
        "bin",
        "sh",
        "ps1",
        "jar",
    ]

    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "300"))
    REDIS_CACHE_ENABLED = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"

    CACHE_KEY_PREFIX = "label_portal"
    CACHE_KEY_RECORD_LIST = "record_list"
    CACHE_KEY_RECORD_SINGLE = "record_single"
