from datetime import datetime
from zoneinfo import ZoneInfo

from .extensions import db


BJ_TZ = ZoneInfo("Asia/Shanghai")


def beijing_now() -> datetime:
    return datetime.now(BJ_TZ).replace(tzinfo=None)


class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="active")
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)


class DbConfig(db.Model):
    __tablename__ = "db_config"

    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(128), nullable=False, default="db")
    port = db.Column(db.Integer, nullable=False, default=3306)
    username = db.Column(db.String(128), nullable=False, default="root")
    password_encrypted = db.Column(db.String(255), nullable=False)
    database_name = db.Column(db.String(128), nullable=False, default="label_portal")
    table_prefix_rule = db.Column(db.String(64), nullable=False, default="page_{page_id}_")
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    upload_size_limit_mb = db.Column(db.Integer, nullable=False, default=100)
    allowed_extensions = db.Column(db.JSON, nullable=False)
    allowed_mime_types = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)


class LoginAudit(db.Model):
    __tablename__ = "login_audit"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    attempted_at = db.Column(db.DateTime, nullable=False, default=beijing_now, index=True)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    admin = db.relationship("Admin", lazy=True)


class PageGroup(db.Model):
    __tablename__ = "page_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    status = db.Column(db.String(16), nullable=False, default="enabled", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)


class PageTag(db.Model):
    __tablename__ = "page_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True, index=True)
    color = db.Column(db.String(16), nullable=False, default="blue")
    status = db.Column(db.String(16), nullable=False, default="enabled", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)


page_group_association = db.Table(
    "page_group_association",
    db.Column("page_id", db.Integer, db.ForeignKey("business_pages.id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("page_groups.id"), primary_key=True),
)

page_tag_association = db.Table(
    "page_tag_association",
    db.Column("page_id", db.Integer, db.ForeignKey("business_pages.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("page_tags.id"), primary_key=True),
)


class BusinessPage(db.Model):
    __tablename__ = "business_pages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    developer = db.Column(db.String(64), nullable=False)
    main_page = db.Column(db.String(255), nullable=False)
    storage_folder = db.Column(db.String(255), nullable=False)
    route_path = db.Column(db.String(255), nullable=False, unique=True)
    table_prefix = db.Column(db.String(40), nullable=False, unique=True)
    table_name = db.Column(db.String(80), nullable=False, unique=True)
    api_token_hash = db.Column(db.String(64), nullable=False)
    qrcode_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="enabled", index=True)
    uploader_admin_id = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=beijing_now, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=beijing_now, onupdate=beijing_now)

    uploader = db.relationship("Admin", lazy=True)
    groups = db.relationship(
        "PageGroup",
        secondary=page_group_association,
        lazy="selectin",
        backref=db.backref("pages", lazy="selectin"),
    )
    tags = db.relationship(
        "PageTag",
        secondary=page_tag_association,
        lazy="selectin",
        backref=db.backref("pages", lazy="selectin"),
    )
