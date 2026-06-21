from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..extensions import db
from ..models import BusinessPage, PageGroup, PageTag
from ..utils import json_success, to_iso


bp = Blueprint("public", __name__, url_prefix="/api/public")


def _serialize(page: BusinessPage) -> dict:
    return {
        "id": page.id,
        "name": page.name,
        "description": page.description,
        "category": page.category,
        "developer": page.developer,
        "route_path": page.route_path,
        "created_at": to_iso(page.created_at),
        "groups": [{"id": g.id, "name": g.name} for g in page.groups],
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in page.tags],
    }


@bp.get("/pages")
def list_public_pages():
    keyword = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_id = request.args.get("group_id", "").strip()
    tag_ids = request.args.get("tag_ids", "").strip()
    time_sort = request.args.get("time_sort", "newest")

    query = BusinessPage.query.filter(BusinessPage.status == "enabled")

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
    return jsonify(json_success([_serialize(page) for page in pages]))


@bp.get("/categories")
def list_categories():
    rows = db.session.query(BusinessPage.category).filter(BusinessPage.status == "enabled").distinct().all()
    categories = [row[0] for row in rows]
    return jsonify(json_success(categories))


@bp.get("/groups")
def list_public_groups():
    groups = PageGroup.query.filter_by(status="enabled").order_by(PageGroup.sort_order.asc(), PageGroup.id.asc()).all()
    result = [{"id": g.id, "name": g.name, "description": g.description} for g in groups]
    return jsonify(json_success(result))


@bp.get("/tags")
def list_public_tags():
    tags = PageTag.query.filter_by(status="enabled").order_by(PageTag.id.asc()).all()
    result = [{"id": t.id, "name": t.name, "color": t.color} for t in tags]
    return jsonify(json_success(result))
