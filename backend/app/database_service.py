import logging
import re
import time

from sqlalchemy import event, text
from sqlalchemy.exc import (
    DatabaseError,
    DisconnectionError,
    OperationalError,
    ProgrammingError,
    StatementError,
)

from .extensions import db

logger = logging.getLogger(__name__)

MYSQL_GONE_AWAY_PATTERNS = [
    re.compile(r"MySQL server has gone away", re.IGNORECASE),
    re.compile(r"Lost connection to MySQL server", re.IGNORECASE),
    re.compile(r"Connection refused", re.IGNORECASE),
    re.compile(r"Can't connect to MySQL", re.IGNORECASE),
    re.compile(r"Commands out of sync", re.IGNORECASE),
    re.compile(r"Packets out of order", re.IGNORECASE),
    re.compile(r"connection is closed", re.IGNORECASE),
]


def is_connection_error(exc: Exception) -> bool:
    if isinstance(exc, (DisconnectionError, OperationalError)):
        return True
    error_msg = str(exc)
    return any(pattern.search(error_msg) for pattern in MYSQL_GONE_AWAY_PATTERNS)


def safe_db_execute(statement, params=None, timeout=None):
    from flask import current_app

    timeout = timeout or current_app.config.get("DB_QUERY_TIMEOUT", 30)
    max_retries = 3
    retry_count = 0
    last_exc = None

    while retry_count < max_retries:
        try:
            if retry_count > 0:
                logger.warning(
                    "数据库重试第 %d/%d 次", retry_count, max_retries
                )
                try:
                    db.session.execute(text("SELECT 1"))
                    db.session.commit()
                except Exception as ping_exc:
                    logger.warning(
                        "连接健康检查失败，丢弃当前会话：%s", ping_exc
                    )
                    db.session.rollback()
                    db.session.remove()

            result = db.session.execute(statement, params or {})
            return result
        except Exception as exc:
            last_exc = exc
            retry_count += 1
            db.session.rollback()

            if not is_connection_error(exc):
                logger.error(
                    "数据库非连接错误，不进行重试：%s", exc
                )
                raise

            logger.warning(
                "检测到连接错误（第 %d/%d 次）：%s",
                retry_count,
                max_retries,
                exc,
            )

            db.session.remove()

            if retry_count < max_retries:
                backoff = min(0.1 * (2 ** retry_count), 2.0)
                time.sleep(backoff)
                logger.info("等待 %.1f 秒后重试", backoff)

    logger.error(
        "数据库操作在 %d 次重试后仍失败：%s",
        max_retries,
        last_exc,
    )
    raise last_exc


def ping_db() -> bool:
    try:
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        logger.debug("数据库连接健康检查通过")
        return True
    except Exception as exc:
        logger.error("数据库连接健康检查失败：%s", exc)
        db.session.rollback()
        db.session.remove()
        return False


def register_db_event_listeners():
    engine = db.engine

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, connection_record):
        logger.debug("新数据库连接已建立")
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET SESSION wait_timeout = 28800")
            cursor.execute("SET SESSION interactive_timeout = 28800")
            cursor.execute("SET SESSION net_read_timeout = 60")
            cursor.execute("SET SESSION net_write_timeout = 60")
            cursor.close()
            logger.debug("数据库会话超时参数已设置")
        except Exception as exc:
            logger.warning("设置数据库会话参数失败：%s", exc)

    @event.listens_for(engine, "checkout")
    def _on_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("检出数据库连接")
        connection_record.info.setdefault("checkout_count", 0)
        connection_record.info["checkout_count"] += 1

    @event.listens_for(engine, "checkin")
    def _on_checkin(dbapi_connection, connection_record):
        logger.debug("归还数据库连接")

    @event.listens_for(engine, "close")
    def _on_close(dbapi_connection, connection_record):
        logger.debug("关闭数据库连接")
        logger.info(
            "连接关闭，检出次数：%d",
            connection_record.info.get("checkout_count", 0),
        )
