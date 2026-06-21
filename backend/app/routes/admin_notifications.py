from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from ..errors import ApiError
from ..security import admin_required
from ..services.notification_service import (
    get_notifications,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
)
from ..utils import json_success, to_iso


bp = Blueprint("admin_notifications", __name__, url_prefix="/api/admin/notifications")


def _serialize_notification(notification) -> dict:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "content": notification.content,
        "is_read": notification.is_read,
        "admin_id": notification.admin_id,
        "created_at": to_iso(notification.created_at),
        "read_at": to_iso(notification.read_at),
    }


@bp.get("/unread-count")
@admin_required()
def unread_count():
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    count = get_unread_count(admin_id=admin_id)
    return jsonify(json_success({"count": count}))


@bp.get("")
@admin_required()
def list_notifications():
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    only_unread = request.args.get("only_unread", "0") == "1"
    limit = min(int(request.args.get("limit", 50)), 200)

    notifications = get_notifications(
        admin_id=admin_id,
        only_unread=only_unread,
        limit=limit,
    )
    return jsonify(
        json_success([_serialize_notification(n) for n in notifications])
    )


@bp.post("/<int:notification_id>/read")
@admin_required(require_csrf=True)
def read_notification(notification_id: int):
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    notification = mark_as_read(notification_id, admin_id=admin_id)
    if not notification:
        raise ApiError(404, "通知不存在")
    return jsonify(json_success(_serialize_notification(notification), "已标记为已读"))


@bp.post("/read-all")
@admin_required(require_csrf=True)
def read_all_notifications():
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    count = mark_all_as_read(admin_id=admin_id)
    return jsonify(json_success({"count": count}, f"已标记 {count} 条通知为已读"))
