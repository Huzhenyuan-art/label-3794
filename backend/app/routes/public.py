import hashlib
import logging

from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import BusinessPage, PageGroup, PageTag, PageVisit
from ..utils import (
    json_success,
    safe_getattr,
    safe_serialize_iterable,
    serialize_group,
    serialize_groups_collection,
    serialize_tag,
    serialize_tags_collection,
    to_iso,
)

logger = logging.getLogger(__name__)


bp = Blueprint("public", __name__, url_prefix="/api/public")


def _serialize(page: BusinessPage) -> dict:
    try:
        groups = serialize_groups_collection(safe_getattr(page, "groups", []))
    except Exception as exc:
        groups = []

    try:
        tags = serialize_tags_collection(safe_getattr(page, "tags", []))
    except Exception as exc:
        tags = []

    return {
        "id": safe_getattr(page, "id"),
        "name": safe_getattr(page, "name", ""),
        "description": safe_getattr(page, "description", ""),
        "category": safe_getattr(page, "category", ""),
        "developer": safe_getattr(page, "developer", ""),
        "route_path": safe_getattr(page, "route_path", ""),
        "created_at": to_iso(safe_getattr(page, "created_at")),
        "groups": groups,
        "tags": tags,
    }


@bp.get("/pages")
def list_public_pages():
    keyword = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_id = request.args.get("group_id", "").strip()
    tag_ids = request.args.get("tag_ids", "").strip()
    time_sort = request.args.get("time_sort", "newest")

    query = BusinessPage.query.options(
        selectinload(BusinessPage.groups),
        selectinload(BusinessPage.tags),
    ).filter(BusinessPage.status == "enabled")

    if keyword:
        fuzzy = f"%{keyword}%"
        query = query.filter(or_(BusinessPage.name.ilike(fuzzy), BusinessPage.description.ilike(fuzzy)))

    if category:
        query = query.filter(BusinessPage.category == category)

    if group_id:
        try:
            gid = int(group_id)
            query = query.filter(BusinessPage.groups.any(PageGroup.id == gid))
        except ValueError:
            pass

    if tag_ids:
        try:
            tid_list = [int(t) for t in tag_ids.split(",") if t.strip()]
            if tid_list:
                for tid in tid_list:
                    query = query.filter(BusinessPage.tags.any(PageTag.id == tid))
        except ValueError:
            pass

    if time_sort == "oldest":
        query = query.order_by(BusinessPage.created_at.asc())
    else:
        query = query.order_by(BusinessPage.created_at.desc())

    pages = query.all()
    return jsonify(json_success(safe_serialize_iterable(pages, _serialize)))


@bp.get("/categories")
def list_categories():
    rows = db.session.query(BusinessPage.category).filter(BusinessPage.status == "enabled").distinct().all()
    categories = [row[0] for row in rows]
    return jsonify(json_success(categories))


@bp.get("/groups")
def list_public_groups():
    groups = PageGroup.query.filter_by(status="enabled").order_by(PageGroup.sort_order.asc(), PageGroup.id.asc()).all()
    result = []
    for g in safe_serialize_iterable(groups, serialize_group):
        if g.get("id") is not None:
            result.append(
                {
                    "id": g.get("id"),
                    "name": g.get("name", ""),
                    "description": g.get("description", ""),
                }
            )
    return jsonify(json_success(result))


@bp.get("/tags")
def list_public_tags():
    tags = PageTag.query.filter_by(status="enabled").order_by(PageTag.id.asc()).all()
    result = []
    for t in safe_serialize_iterable(tags, serialize_tag):
        if t.get("id") is not None:
            result.append(
                {
                    "id": t.get("id"),
                    "name": t.get("name", ""),
                    "color": t.get("color", "blue"),
                }
            )
    return jsonify(json_success(result))


def _get_visitor_id() -> str:
    ip = request.remote_addr or "unknown"
    user_agent = request.headers.get("User-Agent", "")
    raw = f"{ip}|{user_agent}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


@bp.post("/page-visit")
def record_page_visit():
    try:
        data = request.get_json(silent=True) or {}
        page_id = data.get("page_id")
        referrer = data.get("referrer") or request.headers.get("Referer")

        if not page_id:
            return jsonify(json_success(None, "page_id 不能为空")), 400

        page = BusinessPage.query.get(page_id)
        if not page or page.status != "enabled":
            return jsonify(json_success(None, "页面不存在或已禁用")), 404

        visitor_id = _get_visitor_id()
        ip_address = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")[:500]

        if referrer and len(referrer) > 500:
            referrer = referrer[:500]

        visit = PageVisit(
            page_id=page_id,
            visitor_id=visitor_id,
            referrer=referrer,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(visit)
        db.session.commit()

        return jsonify(json_success({"visit_id": visit.id}, "访问记录成功"))
    except Exception as exc:
        logger.warning("记录页面访问失败: %s", exc)
        db.session.rollback()
        return jsonify(json_success(None, "记录失败")), 500
