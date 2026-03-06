from datetime import datetime
from typing import Any


def to_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def json_success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {
        "message": message,
        "data": data,
    }
