import logging
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import PageVisit, BusinessPage
from ..security import admin_required
from ..utils import json_success, to_iso
from ..models import beijing_now


bp = Blueprint("admin_stats", __name__, url_prefix="/api/admin/stats")
logger = logging.getLogger(__name__)


def _parse_date(date_str: str | None, default: datetime) -> datetime:
    if not date_str:
        return default
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return default


@bp.get("/overview")
@admin_required()
def get_stats_overview():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    now = beijing_now()
    end_date = _parse_date(end_date_str, now)
    start_date = _parse_date(start_date_str, now - timedelta(days=30))

    total_visits = db.session.query(func.count(PageVisit.id)).filter(
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).scalar() or 0

    total_visitors = db.session.query(func.count(func.distinct(PageVisit.visitor_id))).filter(
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).scalar() or 0

    total_pages = db.session.query(func.count(func.distinct(PageVisit.page_id))).filter(
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).scalar() or 0

    return jsonify(json_success({
        "total_visits": total_visits,
        "total_visitors": total_visitors,
        "total_pages": total_pages,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }))


@bp.get("/trend")
@admin_required()
def get_visit_trend():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    now = beijing_now()
    end_date = _parse_date(end_date_str, now)
    start_date = _parse_date(start_date_str, now - timedelta(days=30))

    date_list = []
    current = start_date
    while current.date() <= end_date.date():
        date_list.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    visit_data = db.session.query(
        func.date(PageVisit.visited_at).label("visit_date"),
        func.count(PageVisit.id).label("visit_count"),
        func.count(func.distinct(PageVisit.visitor_id)).label("visitor_count"),
    ).filter(
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).group_by(func.date(PageVisit.visited_at)).all()

    visit_map = {}
    for row in visit_data:
        visit_map[str(row.visit_date)] = {
            "visits": row.visit_count,
            "visitors": row.visitor_count,
        }

    trend = []
    for date_str in date_list:
        data = visit_map.get(date_str, {"visits": 0, "visitors": 0})
        trend.append({
            "date": date_str,
            "visits": data["visits"],
            "visitors": data["visitors"],
        })

    return jsonify(json_success(trend))


@bp.get("/pages/ranking")
@admin_required()
def get_page_ranking():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    limit = request.args.get("limit", 20, type=int)
    sort_by = request.args.get("sort_by", "visits")

    now = beijing_now()
    end_date = _parse_date(end_date_str, now)
    start_date = _parse_date(start_date_str, now - timedelta(days=30))

    query = db.session.query(
        PageVisit.page_id,
        func.count(PageVisit.id).label("visit_count"),
        func.count(func.distinct(PageVisit.visitor_id)).label("visitor_count"),
        func.max(PageVisit.visited_at).label("last_visit"),
    ).filter(
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).group_by(PageVisit.page_id)

    if sort_by == "visitors":
        query = query.order_by(desc("visitor_count"))
    else:
        query = query.order_by(desc("visit_count"))

    rows = query.limit(limit).all()

    ranking = []
    for row in rows:
        page = BusinessPage.query.get(row.page_id)
        if page:
            ranking.append({
                "page_id": row.page_id,
                "page_name": page.name,
                "route_path": page.route_path,
                "visits": row.visit_count,
                "visitors": row.visitor_count,
                "last_visit": to_iso(row.last_visit),
            })

    return jsonify(json_success(ranking))


@bp.get("/referrers")
@admin_required()
def get_referrer_stats():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    limit = request.args.get("limit", 20, type=int)

    now = beijing_now()
    end_date = _parse_date(end_date_str, now)
    start_date = _parse_date(start_date_str, now - timedelta(days=30))

    rows = db.session.query(
        PageVisit.referrer,
        func.count(PageVisit.id).label("visit_count"),
        func.count(func.distinct(PageVisit.visitor_id)).label("visitor_count"),
    ).filter(
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
        PageVisit.referrer.isnot(None),
        PageVisit.referrer != "",
    ).group_by(PageVisit.referrer).order_by(desc("visit_count")).limit(limit).all()

    referrers = []
    for row in rows:
        referrers.append({
            "referrer": row.referrer,
            "visits": row.visit_count,
            "visitors": row.visitor_count,
        })

    return jsonify(json_success(referrers))


@bp.get("/pages/<int:page_id>")
@admin_required()
def get_page_stats_detail(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        from ..errors import ApiError
        raise ApiError(404, "页面不存在")

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    now = beijing_now()
    end_date = _parse_date(end_date_str, now)
    start_date = _parse_date(start_date_str, now - timedelta(days=30))

    total_visits = db.session.query(func.count(PageVisit.id)).filter(
        PageVisit.page_id == page_id,
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).scalar() or 0

    total_visitors = db.session.query(func.count(func.distinct(PageVisit.visitor_id))).filter(
        PageVisit.page_id == page_id,
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).scalar() or 0

    last_visit = db.session.query(func.max(PageVisit.visited_at)).filter(
        PageVisit.page_id == page_id,
    ).scalar()

    date_list = []
    current = start_date
    while current.date() <= end_date.date():
        date_list.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    daily_data = db.session.query(
        func.date(PageVisit.visited_at).label("visit_date"),
        func.count(PageVisit.id).label("visit_count"),
        func.count(func.distinct(PageVisit.visitor_id)).label("visitor_count"),
    ).filter(
        PageVisit.page_id == page_id,
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
    ).group_by(func.date(PageVisit.visited_at)).all()

    daily_map = {str(row.visit_date): {
        "visits": row.visit_count,
        "visitors": row.visitor_count,
    } for row in daily_data}

    trend = []
    for date_str in date_list:
        data = daily_map.get(date_str, {"visits": 0, "visitors": 0})
        trend.append({
            "date": date_str,
            "visits": data["visits"],
            "visitors": data["visitors"],
        })

    referrer_rows = db.session.query(
        PageVisit.referrer,
        func.count(PageVisit.id).label("visit_count"),
    ).filter(
        PageVisit.page_id == page_id,
        PageVisit.visited_at >= start_date,
        PageVisit.visited_at <= end_date,
        PageVisit.referrer.isnot(None),
        PageVisit.referrer != "",
    ).group_by(PageVisit.referrer).order_by(desc("visit_count")).limit(10).all()

    top_referrers = [
        {"referrer": row.referrer, "visits": row.visit_count}
        for row in referrer_rows
    ]

    return jsonify(json_success({
        "page_id": page_id,
        "page_name": page.name,
        "total_visits": total_visits,
        "total_visitors": total_visitors,
        "last_visit": to_iso(last_visit),
        "trend": trend,
        "top_referrers": top_referrers,
    }))
