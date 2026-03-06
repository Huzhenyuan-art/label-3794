import logging
from typing import Any

from flask import jsonify
from pydantic import ValidationError


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, details: Any | None = None) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)


logger = logging.getLogger(__name__)


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        payload = {"message": exc.message}
        if exc.details is not None:
            payload["details"] = exc.details
        return jsonify(payload), exc.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({"message": "请求参数校验失败", "details": exc.errors()}), 422

    @app.errorhandler(413)
    def handle_too_large(_exc):
        return jsonify({"message": "上传文件过大"}), 413

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception("Unexpected error: %s", exc)
        return jsonify({"message": "服务器内部错误"}), 500
