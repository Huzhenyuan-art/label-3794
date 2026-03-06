from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request

from ..errors import ApiError
from ..models import BusinessPage
from ..schemas import DataRecordCreatePayload, DataRecordUpdatePayload
from ..security import hash_token
from ..services.dynamic_table_service import (
    create_record,
    delete_record_by_id,
    get_record,
    list_records,
    update_record,
)
from ..utils import json_success, to_iso


bp = Blueprint("data_api", __name__, url_prefix="/api/data")


def _to_dict(row) -> dict:
    return {
        "id": row["id"],
        "record_key": row["record_key"],
        "payload": row["payload"],
        "created_at": to_iso(row["created_at"]),
        "updated_at": to_iso(row["updated_at"]),
    }


def _authorize_page(page: BusinessPage) -> None:
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        if claims and claims.get("role") == "admin":
            return
    except Exception:
        pass

    page_token = request.headers.get("X-Page-Token", "")
    if not page_token or hash_token(page_token) != page.api_token_hash:
        raise ApiError(401, "缺少有效的业务页面访问 Token")


@bp.get("/<int:page_id>/records")
def page_records(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    limit = min(int(request.args.get("limit", 50)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    rows = list_records(page.table_name, limit=limit, offset=offset)

    return jsonify(json_success([_to_dict(row) for row in rows]))


@bp.post("/<int:page_id>/records")
def create_page_record(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    payload = DataRecordCreatePayload.model_validate(request.get_json(silent=True) or {})
    record = create_record(page.table_name, payload.record_key, payload.payload)
    return jsonify(json_success(_to_dict(record), "记录创建成功")), 201


@bp.get("/<int:page_id>/records/<int:record_id>")
def get_page_record(page_id: int, record_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    record = get_record(page.table_name, record_id)
    return jsonify(json_success(_to_dict(record)))


@bp.put("/<int:page_id>/records/<int:record_id>")
@bp.patch("/<int:page_id>/records/<int:record_id>")
def update_page_record(page_id: int, record_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    payload = DataRecordUpdatePayload.model_validate(request.get_json(silent=True) or {})
    record = update_record(page.table_name, record_id, payload.record_key, payload.payload)
    return jsonify(json_success(_to_dict(record), "记录更新成功"))


@bp.delete("/<int:page_id>/records/<int:record_id>")
def delete_page_record(page_id: int, record_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    delete_record_by_id(page.table_name, record_id)
    return jsonify(json_success(message="记录删除成功"))
