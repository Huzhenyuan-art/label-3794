from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt

from ..errors import ApiError
from ..extensions import db
from ..models import Admin, LoginAudit, beijing_now
from ..schemas import LoginPayload
from ..security import admin_required, generate_csrf_token, verify_password
from ..services.notification_service import NOTIFICATION_TYPES, create_notification
from ..utils import json_success, to_iso


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _record_login_audit(username: str, success: bool, reason: str | None, ip: str | None) -> None:
    db.session.add(LoginAudit(username=username, success=success, reason=reason, ip_address=ip))


@bp.post("/admin/login")
def admin_login():
    payload = LoginPayload.model_validate(request.get_json(silent=True) or {})
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    admin = Admin.query.filter_by(username=payload.username).first()
    now = beijing_now()

    if not admin:
        _record_login_audit(payload.username, False, "用户不存在", ip)
        db.session.commit()
        raise ApiError(401, "用户名或密码错误")

    if admin.locked_until and admin.locked_until > now:
        _record_login_audit(payload.username, False, "账号已锁定", ip)
        db.session.commit()
        raise ApiError(423, f"登录失败次数过多，请于 {to_iso(admin.locked_until)} 后重试")

    if not verify_password(payload.password, admin.password_hash):
        admin.failed_login_attempts += 1
        reason = "密码错误"
        if admin.failed_login_attempts >= current_app.config["MAX_LOGIN_ATTEMPTS"]:
            admin.locked_until = now + timedelta(minutes=current_app.config["LOGIN_LOCK_MINUTES"])
            reason = "连续登录失败，账号已临时锁定"
            create_notification(
                notification_type=NOTIFICATION_TYPES["ACCOUNT_LOCKED"],
                title="管理员账号被锁定",
                content=f"管理员账号「{admin.username}」因连续登录失败次数过多，已被临时锁定至 {to_iso(admin.locked_until)}。",
                admin_id=admin.id,
            )

        _record_login_audit(payload.username, False, reason, ip)
        db.session.commit()
        raise ApiError(401, "用户名或密码错误")

    admin.failed_login_attempts = 0
    admin.locked_until = None
    admin.last_login_at = now

    csrf_token = generate_csrf_token()
    token = create_access_token(
        identity=str(admin.id),
        additional_claims={"role": "admin", "admin_id": admin.id, "csrf": csrf_token},
    )

    _record_login_audit(payload.username, True, "登录成功", ip)
    db.session.commit()

    return jsonify(
        json_success(
            {
                "access_token": token,
                "csrf_token": csrf_token,
                "admin": {
                    "id": admin.id,
                    "username": admin.username,
                    "last_login_at": to_iso(admin.last_login_at),
                },
            },
            "登录成功",
        )
    )


@bp.get("/admin/me")
@admin_required()
def admin_me():
    claims = get_jwt()
    admin = Admin.query.get(claims.get("admin_id"))
    if not admin:
        raise ApiError(404, "管理员不存在")

    return jsonify(
        json_success(
            {
                "id": admin.id,
                "username": admin.username,
                "last_login_at": to_iso(admin.last_login_at),
                "created_at": to_iso(admin.created_at),
            }
        )
    )
