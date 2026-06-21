import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from pydantic import ValidationError

from ..errors import ApiError
from ..models import BusinessPage
from ..schemas import DataRecordCreatePayload, DataRecordUpdatePayload, PayloadFilterCondition
from ..security import hash_token
from ..services.cache_service import cache_service
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


MAX_RECORD_KEY_PREFIX_LENGTH = 128
MAX_PAYLOAD_FILTERS = 20


@bp.get("/<int:page_id>/records")
def page_records(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    limit = min(int(request.args.get("limit", 50)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    record_key_prefix = request.args.get("record_key_prefix") or None
    if record_key_prefix and len(record_key_prefix) > MAX_RECORD_KEY_PREFIX_LENGTH:
        raise ApiError(422, "record_key_prefix 长度不得超过 {} 字符".format(MAX_RECORD_KEY_PREFIX_LENGTH))

    payload_filters = None
    raw_filters = request.args.get("payload_filters")
    if raw_filters:
        try:
            parsed = json.loads(raw_filters)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ApiError(422, "payload_filters 不是合法的 JSON") from exc
        if not isinstance(parsed, list):
            raise ApiError(422, "payload_filters 必须为 JSON 数组")
        if len(parsed) > MAX_PAYLOAD_FILTERS:
            raise ApiError(422, "payload_filters 最多允许 {} 个条件".format(MAX_PAYLOAD_FILTERS))
        try:
            payload_filters = [PayloadFilterCondition.model_validate(item) for item in parsed]
        except ValidationError as exc:
            raise ApiError(422, "payload_filters 格式校验失败", details=exc.errors()) from exc

    cache_params = {
        "limit": limit,
        "offset": offset,
        "record_key_prefix": record_key_prefix,
        "payload_filters": raw_filters,
    }
    cache_key = cache_service.make_record_list_key(page_id, cache_params)
    cached = cache_service.get(cache_key)
    if cached is not None:
        return jsonify(json_success(cached))

    rows, total = list_records(
        page.table_name,
        limit=limit,
        offset=offset,
        record_key_prefix=record_key_prefix,
        payload_filters=payload_filters,
    )

    result = {
        "records": [_to_dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
    cache_service.set(cache_key, result)

    return jsonify(json_success(result))


@bp.post("/<int:page_id>/records")
def create_page_record(page_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    payload = DataRecordCreatePayload.model_validate(request.get_json(silent=True) or {})
    record = create_record(page.table_name, payload.record_key, payload.payload)
    cache_service.invalidate_page_cache(page_id)
    return jsonify(json_success(_to_dict(record), "记录创建成功")), 201


@bp.get("/<int:page_id>/records/<int:record_id>")
def get_page_record(page_id: int, record_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    cache_key = cache_service.make_record_single_key(page_id, record_id)
    cached = cache_service.get(cache_key)
    if cached is not None:
        return jsonify(json_success(cached))

    record = get_record(page.table_name, record_id)
    result = _to_dict(record)
    cache_service.set(cache_key, result)
    return jsonify(json_success(result))


@bp.put("/<int:page_id>/records/<int:record_id>")
@bp.patch("/<int:page_id>/records/<int:record_id>")
def update_page_record(page_id: int, record_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    payload = DataRecordUpdatePayload.model_validate(request.get_json(silent=True) or {})
    record = update_record(page.table_name, record_id, payload.record_key, payload.payload)
    cache_service.invalidate_page_cache(page_id)
    return jsonify(json_success(_to_dict(record), "记录更新成功"))


@bp.delete("/<int:page_id>/records/<int:record_id>")
def delete_page_record(page_id: int, record_id: int):
    page = BusinessPage.query.get(page_id)
    if not page:
        raise ApiError(404, "业务页面不存在")
    _authorize_page(page)

    delete_record_by_id(page.table_name, record_id)
    cache_service.invalidate_page_cache(page_id)
    return jsonify(json_success(message="记录删除成功"))
