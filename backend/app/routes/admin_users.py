from flask import Blueprint, jsonify, request

from ..errors import ApiError
from ..extensions import db
from ..models import User
from ..schemas import UserCreatePayload, UserUpdatePayload
from ..security import admin_required, hash_password
from ..utils import json_success, to_iso


bp = Blueprint("admin_users", __name__, url_prefix="/api/admin/users")


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


@bp.get("")
@admin_required()
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify(json_success([_serialize_user(user) for user in users]))


@bp.post("")
@admin_required(require_csrf=True)
def create_user():
    payload = UserCreatePayload.model_validate(request.get_json(silent=True) or {})

    if User.query.filter_by(username=payload.username).first():
        raise ApiError(409, "用户名已存在")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        status=payload.status,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(json_success(_serialize_user(user), "用户创建成功")), 201


@bp.put("/<int:user_id>")
@admin_required(require_csrf=True)
def update_user(user_id: int):
    payload = UserUpdatePayload.model_validate(request.get_json(silent=True) or {})
    user = User.query.get(user_id)
    if not user:
        raise ApiError(404, "用户不存在")

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.status is not None:
        user.status = payload.status
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.session.commit()
    return jsonify(json_success(_serialize_user(user), "用户更新成功"))


@bp.delete("/<int:user_id>")
@admin_required(require_csrf=True)
def delete_user(user_id: int):
    user = User.query.get(user_id)
    if not user:
        raise ApiError(404, "用户不存在")

    db.session.delete(user)
    db.session.commit()
    return jsonify(json_success(message="用户删除成功"))
