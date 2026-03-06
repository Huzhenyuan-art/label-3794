from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..extensions import db
from ..models import BusinessPage
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
    }


@bp.get("/pages")
def list_public_pages():
    keyword = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    time_sort = request.args.get("time_sort", "newest")

    query = BusinessPage.query.filter(BusinessPage.status == "enabled")

    if keyword:
        fuzzy = f"%{keyword}%"
        query = query.filter(or_(BusinessPage.name.ilike(fuzzy), BusinessPage.description.ilike(fuzzy)))

    if category:
        query = query.filter(BusinessPage.category == category)

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
