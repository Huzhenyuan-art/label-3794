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
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "Q8mCU8FlS8aM2O7uTvN9L0n8I4n7hDq8k1P7qQ6Kf-I=")

    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))

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
