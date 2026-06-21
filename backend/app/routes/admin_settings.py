from urllib.parse import quote_plus

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt
from sqlalchemy import text

from ..errors import ApiError
from ..extensions import db
from ..models import Admin, DbConfig, SystemSetting
from ..schemas import ChangePasswordPayload, DbConfigPayload, SqlExecPayload, SystemSettingPayload
from ..security import admin_required, decrypt_text, encrypt_text, hash_password, verify_password
from ..services.notification_service import NOTIFICATION_TYPES, create_notification
from ..utils import json_success, to_iso


bp = Blueprint("admin_settings", __name__, url_prefix="/api/admin/settings")


def _serialize_setting(setting: SystemSetting) -> dict:
    return {
        "upload_size_limit_mb": setting.upload_size_limit_mb,
        "allowed_extensions": setting.allowed_extensions,
        "allowed_mime_types": setting.allowed_mime_types,
        "updated_at": to_iso(setting.updated_at),
    }


def _serialize_db_config(config: DbConfig) -> dict:
    return {
        "host": config.host,
        "port": config.port,
        "username": config.username,
        "password_masked": "******",
        "database_name": config.database_name,
        "table_prefix_rule": config.table_prefix_rule,
        "updated_at": to_iso(config.updated_at),
    }


def _apply_db_config_to_engine(config: DbConfig) -> None:
    """
    将 db_config 表中更新的配置应用到 SQLAlchemy 运行时连接。
    更新 engine 的连接池，使后续连接使用新的数据库配置。
    """
    try:
        raw_password = decrypt_text(config.password_encrypted)
        new_uri = (
            f"mysql+pymysql://{config.username}:{quote_plus(raw_password)}"
            f"@{config.host}:{config.port}/{config.database_name}?charset=utf8mb4"
        )

        # 关闭现有连接池中的所有连接
        db.engine.dispose()

        # 更新 app 配置，使后续引擎使用新 URI
        current_app.config["SQLALCHEMY_DATABASE_URI"] = new_uri

        # 验证新连接是否可用
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    except Exception as exc:
        raise ApiError(400, f"数据库连接验证失败: {str(exc)}") from exc


@bp.get("/overview")
@admin_required()
def get_overview():
    setting = SystemSetting.query.first()
    config = DbConfig.query.first()
    if not setting or not config:
        raise ApiError(500, "系统配置初始化异常")

    return jsonify(
        json_success(
            {
                "system_setting": _serialize_setting(setting),
                "db_config": _serialize_db_config(config),
            }
        )
    )


@bp.put("/system")
@admin_required(require_csrf=True)
def update_system_setting():
    payload = SystemSettingPayload.model_validate(request.get_json(silent=True) or {})
    setting = SystemSetting.query.first()
    if not setting:
        raise ApiError(500, "系统配置初始化异常")

    setting.upload_size_limit_mb = payload.upload_size_limit_mb
    setting.allowed_extensions = payload.allowed_extensions
    setting.allowed_mime_types = payload.allowed_mime_types

    db.session.commit()
    return jsonify(json_success(_serialize_setting(setting), "系统配置更新成功"))


@bp.put("/db-config")
@admin_required(require_csrf=True)
def update_db_config():
    payload = DbConfigPayload.model_validate(request.get_json(silent=True) or {})
    config = DbConfig.query.first()
    if not config:
        raise ApiError(500, "数据库配置初始化异常")

    config.host = payload.host
    config.port = payload.port
    config.username = payload.username
    config.password_encrypted = encrypt_text(payload.password)
    config.database_name = payload.database_name
    config.table_prefix_rule = payload.table_prefix_rule

    db.session.commit()

    # 将更新后的配置应用到运行时连接
    _apply_db_config_to_engine(config)

    return jsonify(json_success(_serialize_db_config(config), "数据库配置更新成功，已切换运行时连接"))


@bp.post("/password")
@admin_required(require_csrf=True)
def change_admin_password():
    payload = ChangePasswordPayload.model_validate(request.get_json(silent=True) or {})
    claims = get_jwt()
    admin = Admin.query.get(claims.get("admin_id"))
    if not admin:
        raise ApiError(404, "管理员不存在")

    if not verify_password(payload.old_password, admin.password_hash):
        raise ApiError(400, "旧密码错误")

    admin.password_hash = hash_password(payload.new_password)
    db.session.commit()
    return jsonify(json_success(message="管理员密码更新成功"))


@bp.post("/sql/query")
@admin_required(require_csrf=True)
def execute_sql_query():
    payload = SqlExecPayload.model_validate(request.get_json(silent=True) or {})
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    try:
        result = db.session.execute(text(payload.sql)).mappings().all()
        rows = [dict(row) for row in result][:200]
        return jsonify(json_success({"rows": rows, "row_count": len(rows)}, "SQL 执行成功"))
    except Exception as exc:
        db.session.rollback()
        truncated_sql = payload.sql[:100] + "..." if len(payload.sql) > 100 else payload.sql
        create_notification(
            notification_type=NOTIFICATION_TYPES["SQL_ERROR"],
            title="SQL 执行报错",
            content=f"SQL 执行失败：{str(exc)}\nSQL 语句：{truncated_sql}",
            admin_id=admin_id,
        )
        raise ApiError(400, f"SQL 执行失败: {str(exc)}")


@bp.get("/db-password-preview")
@admin_required()
def get_decrypted_password_preview():
    """
    仅用于验证配置是否正确，返回脱敏后的密码长度信息。
    """
    config = DbConfig.query.first()
    if not config:
        raise ApiError(500, "数据库配置初始化异常")
    raw = decrypt_text(config.password_encrypted)
    return jsonify(json_success({"password_length": len(raw)}))
