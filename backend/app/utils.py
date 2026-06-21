import logging
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


def to_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, AttributeError) as exc:
        logger.warning("日期序列化失败，返回 None：%s (原始值=%r)", exc, dt)
        return None


def json_success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {
        "message": message,
        "data": data,
    }


def safe_getattr(obj: Any, field: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        value = getattr(obj, field, default)
        return value if value is not None else default
    except Exception as exc:
        logger.warning(
            "获取对象属性失败：%s.%s -> %s (对象类型=%s)",
            type(obj).__name__,
            field,
            exc,
            type(obj).__name__,
        )
        return default


def safe_list(collection: Any) -> list:
    if collection is None:
        return []
    try:
        return list(collection)
    except Exception as exc:
        logger.warning("集合转列表失败，返回空列表：%s", exc)
        return []


def safe_serialize_related(obj: Any, fields: list[tuple[str, Any]]) -> dict | None:
    if obj is None:
        return None
    result = {}
    try:
        for field, default in fields:
            result[field] = safe_getattr(obj, field, default)
        return result
    except Exception as exc:
        logger.warning(
            "关联对象序列化失败：%s -> %s (对象类型=%s)",
            fields,
            exc,
            type(obj).__name__,
        )
        return None


def serialize_group(group: Any) -> dict | None:
    return safe_serialize_related(
        group,
        [
            ("id", None),
            ("name", ""),
            ("description", ""),
            ("sort_order", 0),
            ("status", ""),
        ],
    )


def serialize_tag(tag: Any) -> dict | None:
    return safe_serialize_related(
        tag,
        [
            ("id", None),
            ("name", ""),
            ("color", "blue"),
            ("status", ""),
        ],
    )


def serialize_groups_collection(groups: Any) -> list[dict]:
    result = []
    for g in safe_list(groups):
        item = serialize_group(g)
        if item is not None and item.get("id") is not None:
            result.append(item)
    return result


def serialize_tags_collection(tags: Any) -> list[dict]:
    result = []
    for t in safe_list(tags):
        item = serialize_tag(t)
        if item is not None and item.get("id") is not None:
            result.append(item)
    return result


def safe_serialize_iterable(iterable: Any, serializer) -> list:
    result = []
    for item in safe_list(iterable):
        try:
            serialized = serializer(item)
            if serialized is not None:
                result.append(serialized)
        except Exception as exc:
            logger.warning(
                "迭代序列化失败：%s (元素类型=%s)",
                exc,
                type(item).__name__,
            )
    return result
