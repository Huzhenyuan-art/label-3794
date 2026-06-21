import base64

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt

from ..errors import ApiError
from ..extensions import db
from ..models import BusinessPage, LoginAudit, User, beijing_now
from ..schemas import (
    LoginPayload,
    UserChangePasswordPayload,
    UserProfileUpdatePayload,
)
from ..security import generate_csrf_token, user_required, verify_password, hash_password
from ..services.captcha_service import CAPTCHA_THRESHOLD, consume_captcha, create_captcha, verify_captcha
from ..utils import json_success, to_iso


bp = Blueprint("user_portal", __name__, url_prefix="/api/user")


def _record_login_audit(username: str, success: bool, reason: str | None, ip: str | None) -> None:
    db.session.add(LoginAudit(username=username, success=success, reason=reason, ip_address=ip))


def _serialize_page(page: BusinessPage) -> dict:
    return {
        "id": page.id,
        "name": page.name,
        "description": page.description,
        "category": page.category,
        "developer": page.developer,
        "route_path": page.route_path,
        "status": page.status,
        "created_at": to_iso(page.created_at),
        "updated_at": to_iso(page.updated_at),
    }


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "status": user.status,
        "last_login_at": to_iso(user.last_login_at),
        "created_at": to_iso(user.created_at),
        "updated_at": to_iso(user.updated_at),
    }


@bp.get("/captcha")
def user_captcha():
    captcha_id, image_bytes = create_captcha()
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:image/png;base64,{image_base64}"
    return jsonify(json_success({"captcha_id": captcha_id, "image": data_url}, "验证码已生成"))


@bp.post("/login")
def user_login():
    payload = LoginPayload.model_validate(request.get_json(silent=True) or {})
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    threshold = CAPTCHA_THRESHOLD

    user = User.query.filter_by(username=payload.username).first()
    now = beijing_now()

    if not user:
        _record_login_audit(payload.username, False, "用户不存在", ip)
        db.session.commit()
        raise ApiError(401, "用户名或密码错误", extra={"require_captcha": False})

    if user.status != "active":
        _record_login_audit(payload.username, False, "账号已被禁用", ip)
        db.session.commit()
        raise ApiError(403, "账号已被禁用，请联系管理员")

    captcha_ok = True
    if payload.captcha_id or payload.captcha_code:
        if not payload.captcha_id or not payload.captcha_code:
            _record_login_audit(payload.username, False, "验证码缺失", ip)
            db.session.commit()
            raise ApiError(401, "请输入验证码", extra={"require_captcha": True})

        captcha_ok, captcha_msg = verify_captcha(payload.captcha_id, payload.captcha_code)
        if not captcha_ok:
            _record_login_audit(payload.username, False, f"验证码错误({captcha_msg})", ip)
            db.session.commit()
            raise ApiError(401, captcha_msg, extra={"require_captcha": True})

    if not verify_password(payload.password, user.password_hash):
        _record_login_audit(payload.username, False, "密码错误", ip)
        db.session.commit()
        raise ApiError(401, "用户名或密码错误", extra={"require_captcha": False})

    if payload.captcha_id:
        consume_captcha(payload.captcha_id)

    user.last_login_at = now
    db.session.commit()

    csrf_token = generate_csrf_token()
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": "user", "user_id": user.id, "csrf": csrf_token},
    )

    _record_login_audit(payload.username, True, "登录成功", ip)
    db.session.commit()

    return jsonify(
        json_success(
            {
                "access_token": token,
                "csrf_token": csrf_token,
                "user": _serialize_user(user),
            },
            "登录成功",
        )
    )


@bp.get("/me")
@user_required()
def user_me():
    claims = get_jwt()
    user = User.query.get(claims.get("user_id"))
    if not user:
        raise ApiError(404, "用户不存在")

    return jsonify(json_success(_serialize_user(user)))


@bp.get("/authorized-pages")
@user_required()
def user_authorized_pages():
    claims = get_jwt()
    user = User.query.get(claims.get("user_id"))
    if not user:
        raise ApiError(404, "用户不存在")

    pages = [p for p in user.authorized_pages if p.status == "enabled"]
    pages.sort(key=lambda p: p.created_at, reverse=True)

    return jsonify(json_success([_serialize_page(page) for page in pages]))


@bp.put("/profile")
@user_required(require_csrf=True)
def user_update_profile():
    claims = get_jwt()
    user = User.query.get(claims.get("user_id"))
    if not user:
        raise ApiError(404, "用户不存在")

    payload = UserProfileUpdatePayload.model_validate(request.get_json(silent=True) or {})

    if payload.display_name is not None:
        user.display_name = payload.display_name.strip() or None

    db.session.commit()
    return jsonify(json_success(_serialize_user(user), "个人资料已更新"))


@bp.post("/change-password")
@user_required(require_csrf=True)
def user_change_password():
    claims = get_jwt()
    user = User.query.get(claims.get("user_id"))
    if not user:
        raise ApiError(404, "用户不存在")

    payload = UserChangePasswordPayload.model_validate(request.get_json(silent=True) or {})

    if not verify_password(payload.old_password, user.password_hash):
        raise ApiError(400, "原密码错误")

    user.password_hash = hash_password(payload.new_password)
    db.session.commit()
    return jsonify(json_success(message="密码修改成功"))
