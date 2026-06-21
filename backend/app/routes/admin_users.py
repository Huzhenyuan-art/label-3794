from flask import Blueprint, jsonify, request

from ..errors import ApiError
from ..extensions import db
from ..models import BusinessPage, User
from ..schemas import UserAuthorizedPagesPayload, UserCreatePayload, UserUpdatePayload
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
        "authorized_page_ids": [p.id for p in user.authorized_pages],
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


@bp.get("/<int:user_id>/authorized-pages")
@admin_required()
def get_user_authorized_pages(user_id: int):
    user = User.query.get(user_id)
    if not user:
        raise ApiError(404, "用户不存在")

    def _simple_page(page: BusinessPage) -> dict:
        return {
            "id": page.id,
            "name": page.name,
            "description": page.description,
            "category": page.category,
            "status": page.status,
            "route_path": page.route_path,
        }

    all_pages = BusinessPage.query.order_by(BusinessPage.created_at.desc()).all()
    authorized_ids = {p.id for p in user.authorized_pages}

    return jsonify(
        json_success(
            {
                "all_pages": [_simple_page(p) for p in all_pages],
                "authorized_page_ids": list(authorized_ids),
            }
        )
    )


@bp.put("/<int:user_id>/authorized-pages")
@admin_required(require_csrf=True)
def update_user_authorized_pages(user_id: int):
    user = User.query.get(user_id)
    if not user:
        raise ApiError(404, "用户不存在")

    payload = UserAuthorizedPagesPayload.model_validate(request.get_json(silent=True) or {})
    pages = BusinessPage.query.filter(BusinessPage.id.in_(payload.page_ids)).all() if payload.page_ids else []

    if len(pages) != len(payload.page_ids):
        raise ApiError(400, "存在无效的页面 ID")

    user.authorized_pages = pages
    db.session.commit()
    return jsonify(json_success(_serialize_user(user), "页面授权已更新"))
