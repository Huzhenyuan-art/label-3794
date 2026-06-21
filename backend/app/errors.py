import logging
from typing import Any

from flask import jsonify
from pydantic import ValidationError
from sqlalchemy.exc import (
    DisconnectionError,
    OperationalError,
    StatementError,
)

from .database_service import is_connection_error


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, details: Any | None = None, extra: dict | None = None) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        self.extra = extra or {}
        super().__init__(message)


logger = logging.getLogger(__name__)


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        payload = {"message": exc.message}
        if exc.details is not None:
            payload["details"] = exc.details
        if exc.extra:
            payload.update(exc.extra)
        return jsonify(payload), exc.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({"message": "请求参数校验失败", "details": exc.errors()}), 422

    @app.errorhandler(413)
    def handle_too_large(_exc):
        return jsonify({"message": "上传文件过大"}), 413

    @app.errorhandler(OperationalError)
    def handle_db_operational_error(exc: OperationalError):
        if is_connection_error(exc):
            logger.error(
                "检测到数据库连接错误 (OperationalError)：%s | 原始错误：%s",
                str(exc),
                exc.orig,
                exc_info=True,
            )
            from .extensions import db

            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                db.session.remove()
            except Exception:
                pass
            return (
                jsonify(
                    {
                        "message": "数据库连接暂时中断，请稍后重试",
                        "error_code": "DB_CONNECTION_ERROR",
                    }
                ),
                503,
            )
        logger.error("数据库操作错误：%s", exc, exc_info=True)
        return jsonify({"message": "数据库操作失败"}), 500

    @app.errorhandler(DisconnectionError)
    def handle_db_disconnection(exc: DisconnectionError):
        logger.error(
            "数据库连接池断开异常：%s", exc, exc_info=True
        )
        from .extensions import db

        try:
            db.session.rollback()
        except Exception:
            pass
        try:
            db.session.remove()
        except Exception:
            pass
        return (
            jsonify(
                {
                    "message": "数据库连接已断开，服务正在恢复，请稍后重试",
                    "error_code": "DB_DISCONNECTED",
                }
            ),
            503,
        )

    @app.errorhandler(StatementError)
    def handle_db_statement_error(exc: StatementError):
        if is_connection_error(exc):
            logger.error(
                "SQL 语句执行期间发生连接中断：%s | 语句：%s | 参数：%s",
                exc,
                getattr(exc, "statement", None),
                getattr(exc, "params", None),
                exc_info=True,
            )
            from .extensions import db

            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                db.session.remove()
            except Exception:
                pass
            return (
                jsonify(
                    {
                        "message": "数据库连接中断，数据可能未保存，请重试",
                        "error_code": "DB_STATEMENT_INTERRUPTED",
                    }
                ),
                503,
            )
        logger.error(
            "SQL 语句执行错误：%s | 语句：%s | 参数：%s",
            exc,
            getattr(exc, "statement", None),
            getattr(exc, "params", None),
            exc_info=True,
        )
        return jsonify({"message": "数据库语句执行失败"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        if is_connection_error(exc):
            logger.error(
                "捕获到未分类的数据库连接异常：%s", exc, exc_info=True
            )
            from .extensions import db

            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                db.session.remove()
            except Exception:
                pass
            return (
                jsonify(
                    {
                        "message": "数据库服务异常，请稍后重试",
                        "error_code": "DB_GENERIC_CONNECTION_ERROR",
                    }
                ),
                503,
            )
        logger.exception("Unexpected error: %s", exc)
        return jsonify({"message": "服务器内部错误"}), 500
