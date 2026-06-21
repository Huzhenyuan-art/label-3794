import logging
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


_FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")

class LoginPayload(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    captcha_id: str | None = Field(default=None, max_length=64)
    captcha_code: str | None = Field(default=None, max_length=16)


class UserCreatePayload(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=64)
    status: str = Field(default="active")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {"active", "disabled"}:
            raise ValueError("status 仅支持 active/disabled")
        return value


class UserUpdatePayload(BaseModel):
    password: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=64)
    status: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        if len(value) < 6:
            raise ValueError("密码长度不得少于 6 位")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in {"active", "disabled"}:
            raise ValueError("status 仅支持 active/disabled")
        return value


class PageCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=2000)
    category: str = Field(min_length=2, max_length=64)
    developer: str = Field(min_length=2, max_length=64)
    main_page: str = Field(min_length=1, max_length=255)

    @field_validator("main_page")
    @classmethod
    def validate_main_page(cls, value: str) -> str:
        if ".." in value or value.startswith("/"):
            raise ValueError("主页面名称非法")
        return value


class PageUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, min_length=2, max_length=2000)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    developer: str | None = Field(default=None, min_length=2, max_length=64)
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in {"enabled", "disabled"}:
            raise ValueError("status 仅支持 enabled/disabled")
        return value


class SystemSettingPayload(BaseModel):
    upload_size_limit_mb: int = Field(ge=1, le=500)
    allowed_extensions: list[str] = Field(min_length=1)
    allowed_mime_types: list[str] = Field(min_length=1)

    @field_validator("allowed_extensions")
    @classmethod
    def normalize_extensions(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in values:
            value = item.strip().lower().lstrip(".")
            if value:
                normalized.append(value)
        if not normalized:
            raise ValueError("allowed_extensions 不能为空")
        return list(dict.fromkeys(normalized))


class ChangePasswordPayload(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class DbConfigPayload(BaseModel):
    host: str = Field(min_length=1, max_length=128)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)
    database_name: str = Field(min_length=1, max_length=128)
    table_prefix_rule: str = Field(min_length=3, max_length=64)


class PayloadFilterCondition(BaseModel):
    field: str = Field(min_length=1, max_length=128)
    op: str = Field(pattern=r"^(eq|neq|gt|gte|lt|lte|like)$")
    value: Any

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        if "." in value:
            raise ValueError("field 不支持嵌套路径")
        if not _FIELD_NAME_PATTERN.match(value):
            raise ValueError("field 仅支持字母、数字、下划线，且必须以字母或下划线开头")
        return value

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Any, info) -> Any:
        op = info.data.get("op")
        if op == "like" and not isinstance(value, str):
            raise ValueError("like 操作符的 value 必须为字符串")
        return value


class DataRecordCreatePayload(BaseModel):
    record_key: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]


class DataRecordUpdatePayload(BaseModel):
    record_key: str | None = Field(default=None, min_length=1, max_length=128)
    payload: dict[str, Any] | None = None


class SqlExecPayload(BaseModel):
    sql: str = Field(min_length=6, max_length=5000)

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, value: str) -> str:
        normalized = value.strip().lower()
        unsafe_tokens = ["drop ", "truncate ", "grant ", "revoke ", "alter user", "create user"]
        if ";" in normalized[:-1]:
            raise ValueError("仅允许执行单条 SQL")
        if not normalized.startswith(("select", "show", "desc", "describe")):
            raise ValueError("当前仅允许执行查询类 SQL")
        if any(token in normalized for token in unsafe_tokens):
            raise ValueError("SQL 语句包含禁止关键字")
        return value


class GroupCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class GroupUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in {"enabled", "disabled"}:
            raise ValueError("status 仅支持 enabled/disabled")
        return value


class TagCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    color: str = Field(default="blue", max_length=16)


class TagUpdatePayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=32)
    color: str | None = Field(default=None, max_length=16)
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in {"enabled", "disabled"}:
            raise ValueError("status 仅支持 enabled/disabled")
        return value


class PageGroupTagBindPayload(BaseModel):
    group_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)
