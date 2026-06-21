import os
import secrets
import time

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt
from sqlalchemy import text

from ..errors import ApiError
from ..extensions import db
from ..models import BusinessPage, DbConfig, PageGroup, PageTag, SystemSetting
from ..schemas import PageCreatePayload, PageGroupTagBindPayload, PageUpdatePayload
from ..security import admin_required, generate_api_token, hash_token
from ..services.dynamic_table_service import drop_dynamic_table, ensure_dynamic_table
from ..services.notification_service import NOTIFICATION_TYPES, create_notification
from ..services.storage_service import delete_assets, store_uploaded_assets
from ..utils import json_success, to_iso


bp = Blueprint("admin_pages", __name__, url_prefix="/api/admin/pages")


def _serialize_page(page: BusinessPage) -> dict:
    return {
        "id": page.id,
        "name": page.name,
        "description": page.description,
        "category": page.category,
        "developer": page.developer,
        "main_page": page.main_page,
        "storage_folder": page.storage_folder,
        "route_path": page.route_path,
        "table_prefix": page.table_prefix,
        "table_name": page.table_name,
        "status": page.status,
        "uploader_admin_id": page.uploader_admin_id,
        "created_at": to_iso(page.created_at),
        "updated_at": to_iso(page.updated_at),
        "groups": [{"id": g.id, "name": g.name} for g in page.groups],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in page.tags],
    }


def _generate_table_prefix(page_id: int | None = None) -> str:
    """
    根据 db_config.table_prefix_rule 生成表前缀。
    如果规则包含 {page_id} 占位符且 page_id 已知，则使用规则模板；
    否则回退到时间戳+随机字符串的方式。
    """
    db_config = DbConfig.query.first()
    if db_config and db_config.table_prefix_rule:
        rule = db_config.table_prefix_rule
        try:
            prefix = rule.format(
                page_id=page_id or int(time.time()),
                timestamp=int(time.time()),
                rand=secrets.token_hex(2),
            )
            # 确保前缀只包含合法字符
            safe_prefix = "".join(c for c in prefix if c.isalnum() or c == "_")
            if safe_prefix:
                return safe_prefix
        except (KeyError, ValueError):
            pass

    # 回退默认策略
    return f"pg{int(time.time())}{secrets.token_hex(2)}"


@bp.get("")
@admin_required()
def list_pages():
    status = request.args.get("status", "all")
    query = BusinessPage.query
    if status in {"enabled", "disabled"}:
        query = query.filter(BusinessPage.status == status)

    pages = query.order_by(BusinessPage.created_at.desc()).all()
    return jsonify(json_success([_serialize_page(page) for page in pages]))


@bp.post("")
@admin_required(require_csrf=True)
def create_page():
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    upload_file = request.files.get("file")
    if not upload_file:
        raise ApiError(400, "请上传页面文件")

    payload = PageCreatePayload.model_validate(
        {
            "name": request.form.get("name", ""),
            "description": request.form.get("description", ""),
            "category": request.form.get("category", ""),
            "developer": request.form.get("developer", ""),
            "main_page": request.form.get("main_page", ""),
        }
    )

    # 获取可选的初始化 SQL
    init_sql = (request.form.get("init_sql") or "").strip()

    setting = SystemSetting.query.first()
    allowed_extensions = (
        setting.allowed_extensions if setting else current_app.config["DEFAULT_ALLOWED_EXTENSIONS"]
    )
    allowed_mime_types = (
        setting.allowed_mime_types
        if setting
        else [
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/zip",
            "application/x-zip-compressed",
            "image/*",
            "text/plain",
        ]
    )
    blocked_extensions = current_app.config["BLOCKED_EXTENSIONS"]
    upload_limit = (setting.upload_size_limit_mb if setting else current_app.config["MAX_UPLOAD_SIZE_MB"]) * 1024 * 1024

    storage_folder = None
    folder_name = None
    page = None
    api_token = None
    try:
        folder_name, storage_folder, route_path = store_uploaded_assets(
            upload_file=upload_file,
            upload_root=current_app.config["UPLOAD_ROOT"],
            main_page=payload.main_page,
            allowed_extensions=allowed_extensions,
            allowed_mime_types=allowed_mime_types,
            blocked_extensions=blocked_extensions,
            max_size_bytes=upload_limit,
        )

        # 先生成一个临时前缀，待 page 录入后再用 page_id 更新
        temp_prefix = _generate_table_prefix()
        while BusinessPage.query.filter_by(table_prefix=temp_prefix).first():
            temp_prefix = _generate_table_prefix()

        table_name = f"{temp_prefix}_records"
        api_token = generate_api_token()

        page = BusinessPage(
            name=payload.name,
            description=payload.description,
            category=payload.category,
            developer=payload.developer,
            main_page=payload.main_page,
            storage_folder=storage_folder,
            route_path=route_path,
            table_prefix=temp_prefix,
            table_name=table_name,
            api_token_hash=hash_token(api_token),
            status="enabled",
            uploader_admin_id=admin_id,
        )

        db.session.add(page)
        db.session.flush()  # 获取 page.id

        # 如果 db_config 规则包含 {page_id}，用真实 page_id 重新生成前缀
        final_prefix = _generate_table_prefix(page_id=page.id)
        if final_prefix != temp_prefix:
            # 确保不重复
            while BusinessPage.query.filter(
                    BusinessPage.table_prefix == final_prefix,
                    BusinessPage.id != page.id
            ).first():
                final_prefix = _generate_table_prefix(page_id=page.id)
            page.table_prefix = final_prefix
            page.table_name = f"{final_prefix}_records"
            table_name = page.table_name

        db.session.commit()
        ensure_dynamic_table(table_name)

        # 执行可选的初始化 SQL
        if init_sql:
            try:
                db.session.execute(text(init_sql))
                db.session.commit()
            except Exception as sql_err:
                db.session.rollback()
                # SQL 执行失败不影响页面创建，但返回警告
                response = _serialize_page(page)
                response["page_api_token"] = api_token
                response["folder_name"] = folder_name
                response["sql_warning"] = f"初始化 SQL 执行失败: {str(sql_err)}"
                return jsonify(json_success(response, "页面创建成功，但初始化 SQL 执行失败")), 201

    except Exception as exc:
        db.session.rollback()
        if storage_folder:
            delete_assets(current_app.config["UPLOAD_ROOT"], storage_folder)
        page_name = payload.name if payload else "未知"
        create_notification(
            notification_type=NOTIFICATION_TYPES["UPLOAD_FAILED"],
            title="业务页面上传失败",
            content=f"上传业务页面「{page_name}」时发生错误：{str(exc)}",
            admin_id=admin_id,
        )
        raise

    response = _serialize_page(page)
    response["page_api_token"] = api_token
    response["folder_name"] = folder_name
    return jsonify(json_success(response, "页面创建成功")), 201


@bp.put("/<int:page_id>")
@admin_required(require_csrf=True)
def update_page(page_id: int):
    payload = PageUpdatePayload.model_validate(request.get_json(silent=True) or {})
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")

    for field in ["name", "description", "category", "developer", "status"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(page, field, value)

    db.session.commit()
    return jsonify(json_success(_serialize_page(page), "页面更新成功"))


@bp.patch("/<int:page_id>/status")
@admin_required(require_csrf=True)
def change_page_status(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")

    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"enabled", "disabled"}:
        raise ApiError(422, "status 仅支持 enabled/disabled")

    page.status = status
    db.session.commit()
    return jsonify(json_success(_serialize_page(page), "状态更新成功"))


@bp.post("/<int:page_id>/reset-token")
@admin_required(require_csrf=True)
def reset_page_token(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")

    new_token = generate_api_token()
    page.api_token_hash = hash_token(new_token)
    db.session.commit()

    data = _serialize_page(page)
    data["page_api_token"] = new_token
    return jsonify(json_success(data, "业务页面 Token 已重置"))


@bp.delete("/<int:page_id>")
@admin_required(require_csrf=True)
def delete_page(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")

    storage_folder = page.storage_folder
    table_name = page.table_name

    db.session.delete(page)
    db.session.commit()

    delete_assets(current_app.config["UPLOAD_ROOT"], storage_folder)
    try:
        drop_dynamic_table(table_name)
    except Exception:
        db.session.rollback()

    return jsonify(json_success(message="页面删除成功"))


@bp.put("/<int:page_id>/groups-tags")
@admin_required(require_csrf=True)
def bind_page_groups_tags(page_id: int):
    payload = PageGroupTagBindPayload.model_validate(request.get_json(silent=True) or {})
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")

    groups = PageGroup.query.filter(PageGroup.id.in_(payload.group_ids)).all() if payload.group_ids else []
    if len(groups) != len(payload.group_ids):
        raise ApiError(400, "存在无效的分组 ID")

    tags = PageTag.query.filter(PageTag.id.in_(payload.tag_ids)).all() if payload.tag_ids else []
    if len(tags) != len(payload.tag_ids):
        raise ApiError(400, "存在无效的标签 ID")

    page.groups = groups
    page.tags = tags
    db.session.commit()
    return jsonify(json_success(_serialize_page(page), "分组与标签绑定成功"))
