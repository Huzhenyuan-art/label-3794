import base64
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt

from ..errors import ApiError
from ..extensions import db
from ..models import Admin, LoginAudit, beijing_now
from ..schemas import LoginPayload
from ..security import admin_required, generate_csrf_token, verify_password
from ..services.captcha_service import CAPTCHA_THRESHOLD, consume_captcha, create_captcha, verify_captcha
from ..services.notification_service import NOTIFICATION_TYPES, create_notification
from ..utils import json_success, to_iso


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _record_login_audit(username: str, success: bool, reason: str | None, ip: str | None) -> None:
    db.session.add(LoginAudit(username=username, success=success, reason=reason, ip_address=ip))


def _handle_password_failed(admin: Admin, username: str, reason: str, ip: str) -> None:
    admin.failed_login_attempts += 1
    now = beijing_now()
    final_reason = reason
    if admin.failed_login_attempts >= current_app.config["MAX_LOGIN_ATTEMPTS"]:
        admin.locked_until = now + timedelta(minutes=current_app.config["LOGIN_LOCK_MINUTES"])
        final_reason = "连续登录失败，账号已临时锁定"
        create_notification(
            notification_type=NOTIFICATION_TYPES["ACCOUNT_LOCKED"],
            title="管理员账号被锁定",
            content=f"管理员账号「{admin.username}」因连续登录失败次数过多，已被临时锁定至 {to_iso(admin.locked_until)}。",
            admin_id=admin.id,
        )

    _record_login_audit(username, False, final_reason, ip)


@bp.get("/admin/captcha")
def admin_captcha():
    captcha_id, image_bytes = create_captcha()
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:image/png;base64,{image_base64}"
    return jsonify(json_success({"captcha_id": captcha_id, "image": data_url}, "验证码已生成"))


@bp.post("/admin/login")
def admin_login():
    payload = LoginPayload.model_validate(request.get_json(silent=True) or {})
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    threshold = current_app.config.get("CAPTCHA_REQUIRED_THRESHOLD", CAPTCHA_THRESHOLD)

    admin = Admin.query.filter_by(username=payload.username).first()
    now = beijing_now()

    if not admin:
        _record_login_audit(payload.username, False, "用户不存在", ip)
        db.session.commit()
        raise ApiError(401, "用户名或密码错误", extra={"require_captcha": False})

    if admin.locked_until and admin.locked_until > now:
        _record_login_audit(payload.username, False, "账号已锁定", ip)
        db.session.commit()
        raise ApiError(
            423,
            f"登录失败次数过多，请于 {to_iso(admin.locked_until)} 后重试",
            extra={"require_captcha": True},
        )

    captcha_ok = True
    captcha_msg = ""
    if admin.failed_login_attempts >= threshold:
        if not payload.captcha_id or not payload.captcha_code:
            _record_login_audit(payload.username, False, "验证码缺失", ip)
            db.session.commit()
            raise ApiError(401, "请输入验证码", extra={"require_captcha": True})

        captcha_ok, captcha_msg = verify_captcha(payload.captcha_id, payload.captcha_code)
        if not captcha_ok:
            _record_login_audit(payload.username, False, f"验证码错误({captcha_msg})", ip)
            db.session.commit()
            raise ApiError(401, captcha_msg, extra={"require_captcha": True})

    if not verify_password(payload.password, admin.password_hash):
        _handle_password_failed(admin, payload.username, "密码错误", ip)
        db.session.commit()
        need_captcha = admin.failed_login_attempts >= threshold
        remaining = current_app.config["MAX_LOGIN_ATTEMPTS"] - admin.failed_login_attempts
        raise ApiError(
            401,
            "用户名或密码错误" if remaining > 0 else "连续登录失败，账号已临时锁定",
            extra={"require_captcha": need_captcha},
        )

    if payload.captcha_id:
        consume_captcha(payload.captcha_id)

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
