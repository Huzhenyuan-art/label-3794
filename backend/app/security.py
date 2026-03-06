import hashlib
import secrets
from functools import wraps

import bcrypt
from cryptography.fernet import Fernet
from flask import current_app, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from .errors import ApiError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(24)


def generate_api_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _fernet() -> Fernet:
    key = current_app.config["ENCRYPTION_KEY"]
    return Fernet(key.encode("utf-8"))


def encrypt_text(raw_text: str) -> str:
    return _fernet().encrypt(raw_text.encode("utf-8")).decode("utf-8")


def decrypt_text(encrypted_text: str) -> str:
    return _fernet().decrypt(encrypted_text.encode("utf-8")).decode("utf-8")


def admin_required(require_csrf: bool = False):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != "admin":
                raise ApiError(403, "需要管理员权限")

            if require_csrf and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                csrf_header = request.headers.get("X-CSRF-Token", "")
                if not csrf_header or csrf_header != claims.get("csrf"):
                    raise ApiError(403, "CSRF 校验失败")

            return func(*args, **kwargs)

        return wrapped

    return decorator
