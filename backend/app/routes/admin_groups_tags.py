from flask import Blueprint, jsonify, request

from ..errors import ApiError
from ..extensions import db
from ..models import PageGroup, PageTag
from ..schemas import GroupCreatePayload, GroupUpdatePayload, TagCreatePayload, TagUpdatePayload
from ..security import admin_required
from ..utils import (
    json_success,
    safe_getattr,
    serialize_group,
    serialize_tag,
    to_iso,
)


bp = Blueprint("admin_groups_tags", __name__, url_prefix="/api/admin")


def _serialize_group(group: PageGroup) -> dict:
    data = serialize_group(group)
    if data is None:
        return {
            "id": None,
            "name": "",
            "description": "",
            "sort_order": 0,
            "status": "",
            "created_at": None,
            "updated_at": None,
        }
    data["created_at"] = to_iso(safe_getattr(group, "created_at"))
    data["updated_at"] = to_iso(safe_getattr(group, "updated_at"))
    return data


def _serialize_tag(tag: PageTag) -> dict:
    data = serialize_tag(tag)
    if data is None:
        return {
            "id": None,
            "name": "",
            "color": "blue",
            "status": "",
            "created_at": None,
            "updated_at": None,
        }
    data["created_at"] = to_iso(safe_getattr(tag, "created_at"))
    data["updated_at"] = to_iso(safe_getattr(tag, "updated_at"))
    return data

@bp.get("/groups")
@admin_required()
def list_groups():
    status = request.args.get("status", "all")
    query = PageGroup.query
    if status in {"enabled", "disabled"}:
        query = query.filter(PageGroup.status == status)
    groups = query.order_by(PageGroup.sort_order.asc(), PageGroup.id.asc()).all()
    return jsonify(json_success([_serialize_group(g) for g in groups]))


@bp.post("/groups")
@admin_required(require_csrf=True)
def create_group():
    payload = GroupCreatePayload.model_validate(request.get_json(silent=True) or {})
    if PageGroup.query.filter_by(name=payload.name).first():
        raise ApiError(400, "分组名称已存在")
    group = PageGroup(
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order,
    )
    db.session.add(group)
    db.session.commit()
    return jsonify(json_success(_serialize_group(group), "分组创建成功")), 201


@bp.put("/groups/<int:group_id>")
@admin_required(require_csrf=True)
def update_group(group_id: int):
    payload = GroupUpdatePayload.model_validate(request.get_json(silent=True) or {})
    group = PageGroup.query.get(group_id)
    if not group:
        raise ApiError(404, "分组不存在")
    if payload.name and payload.name != group.name:
        if PageGroup.query.filter_by(name=payload.name).first():
            raise ApiError(400, "分组名称已存在")
    for field in ["name", "description", "sort_order", "status"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(group, field, value)
    db.session.commit()
    return jsonify(json_success(_serialize_group(group), "分组更新成功"))


@bp.patch("/groups/<int:group_id>/status")
@admin_required(require_csrf=True)
def change_group_status(group_id: int):
    group = PageGroup.query.get(group_id)
    if not group:
        raise ApiError(404, "分组不存在")
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"enabled", "disabled"}:
        raise ApiError(422, "status 仅支持 enabled/disabled")
    group.status = status
    db.session.commit()
    return jsonify(json_success(_serialize_group(group), "状态更新成功"))


@bp.delete("/groups/<int:group_id>")
@admin_required(require_csrf=True)
def delete_group(group_id: int):
    group = PageGroup.query.get(group_id)
    if not group:
        raise ApiError(404, "分组不存在")
    db.session.delete(group)
    db.session.commit()
    return jsonify(json_success(message="分组删除成功"))


@bp.get("/tags")
@admin_required()
def list_tags():
    status = request.args.get("status", "all")
    query = PageTag.query
    if status in {"enabled", "disabled"}:
        query = query.filter(PageTag.status == status)
    tags = query.order_by(PageTag.id.asc()).all()
    return jsonify(json_success([_serialize_tag(t) for t in tags]))


@bp.post("/tags")
@admin_required(require_csrf=True)
def create_tag():
    payload = TagCreatePayload.model_validate(request.get_json(silent=True) or {})
    if PageTag.query.filter_by(name=payload.name).first():
        raise ApiError(400, "标签名称已存在")
    tag = PageTag(
        name=payload.name,
        color=payload.color,
    )
    db.session.add(tag)
    db.session.commit()
    return jsonify(json_success(_serialize_tag(tag), "标签创建成功")), 201


@bp.put("/tags/<int:tag_id>")
@admin_required(require_csrf=True)
def update_tag(tag_id: int):
    payload = TagUpdatePayload.model_validate(request.get_json(silent=True) or {})
    tag = PageTag.query.get(tag_id)
    if not tag:
        raise ApiError(404, "标签不存在")
    if payload.name and payload.name != tag.name:
        if PageTag.query.filter_by(name=payload.name).first():
            raise ApiError(400, "标签名称已存在")
    for field in ["name", "color", "status"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(tag, field, value)
    db.session.commit()
    return jsonify(json_success(_serialize_tag(tag), "标签更新成功"))


@bp.patch("/tags/<int:tag_id>/status")
@admin_required(require_csrf=True)
def change_tag_status(tag_id: int):
    tag = PageTag.query.get(tag_id)
    if not tag:
        raise ApiError(404, "标签不存在")
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"enabled", "disabled"}:
        raise ApiError(422, "status 仅支持 enabled/disabled")
    tag.status = status
    db.session.commit()
    return jsonify(json_success(_serialize_tag(tag), "状态更新成功"))


@bp.delete("/tags/<int:tag_id>")
@admin_required(require_csrf=True)
def delete_tag(tag_id: int):
    tag = PageTag.query.get(tag_id)
    if not tag:
        raise ApiError(404, "标签不存在")
    db.session.delete(tag)
    db.session.commit()
    return jsonify(json_success(message="标签删除成功"))
