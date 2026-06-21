import logging
import os
import time

from sqlalchemy import text

from ..extensions import db
from ..models import Admin, BusinessPage, DbConfig, PageGroup, PageTag, SystemSetting, User
from ..security import encrypt_text, generate_api_token, hash_password, hash_token
from .dynamic_table_service import create_record, ensure_dynamic_table


logger = logging.getLogger(__name__)


def _wait_for_db(app, max_retries: int = 30, retry_interval: int = 2) -> None:
    """
    等待数据库连接就绪，防止 Docker 环境下 MySQL 未完全启动导致启动失败。
    """
    with app.app_context():
        for attempt in range(1, max_retries + 1):
            try:
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                logger.info("数据库连接成功（第 %d 次尝试）", attempt)
                return
            except Exception as exc:
                logger.warning(
                    "数据库连接失败（第 %d/%d 次尝试）：%s，%d 秒后重试...",
                    attempt, max_retries, exc, retry_interval,
                )
                db.session.rollback()
                if attempt == max_retries:
                    logger.error("数据库连接重试次数已达上限，启动失败")
                    raise
                time.sleep(retry_interval)


def _demo_page_html() -> str:
    return """<!doctype html>
<html lang=\"zh-CN\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>示例业务页</title>
    <style>
      body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(120deg, #f8fbff, #eef5ff); margin: 0; padding: 24px; color: #1f2d3d; }
      .card { max-width: 760px; margin: 0 auto; background: #fff; border-radius: 16px; box-shadow: 0 10px 30px rgba(15,23,42,.08); padding: 24px; }
      h1 { margin: 0 0 12px; }
      code { background: #f2f7ff; border-radius: 6px; padding: 2px 6px; }
      ul { line-height: 1.9; }
    </style>
  </head>
  <body>
    <main class=\"card\">
      <h1>示例业务页面已发布</h1>
      <p>当前页面由后台上传模块自动生成路由并托管，说明主站已经具备页面发布能力。</p>
      <ul>
        <li>页面路由由系统生成，如 <code>/pages/xxxx/index.html</code></li>
        <li>业务数据 API：<code>/api/data/{page_id}/records</code></li>
        <li>请求头需携带 <code>X-Page-Token</code></li>
      </ul>
    </main>
  </body>
</html>
"""


def initialize_defaults(app) -> None:
    _wait_for_db(app)
    with app.app_context():
        db.create_all()

        os.makedirs(app.config["UPLOAD_ROOT"], exist_ok=True)

        setting = SystemSetting.query.first()
        if not setting:
            setting = SystemSetting(
                upload_size_limit_mb=app.config["MAX_UPLOAD_SIZE_MB"],
                allowed_extensions=app.config["DEFAULT_ALLOWED_EXTENSIONS"],
                allowed_mime_types=[
                    "text/html",
                    "text/css",
                    "text/javascript",
                    "application/javascript",
                    "application/json",
                    "application/zip",
                    "application/x-zip-compressed",
                    "application/x-httpd-php",
                    "application/x-php",
                    "text/x-php",
                    "image/png",
                    "image/jpeg",
                    "image/gif",
                    "image/svg+xml",
                    "image/webp",
                    "text/plain",
                ],
            )
            db.session.add(setting)

        db_config = DbConfig.query.first()
        if not db_config:
            db_config = DbConfig(
                host=app.config["DB_HOST"],
                port=app.config["DB_PORT"],
                username=app.config["DB_USER"],
                password_encrypted=encrypt_text(app.config["DB_PASSWORD"]),
                database_name=app.config["DB_NAME"],
                table_prefix_rule="page_{page_id}_",
            )
            db.session.add(db_config)

        admin = Admin.query.filter_by(username="admin").first()
        if not admin:
            admin = Admin(username="admin", password_hash=hash_password("123456"))
            db.session.add(admin)

        demo_user = User.query.filter_by(username="demo").first()
        if not demo_user:
            demo_user = User(
                username="demo",
                password_hash=hash_password("123456"),
                display_name="演示用户",
                status="active",
            )
            db.session.add(demo_user)

        db.session.commit()

        default_group = PageGroup.query.filter_by(name="默认分组").first()
        if not default_group:
            default_group = PageGroup(
                name="默认分组",
                description="系统默认分组，用于归类未指定分组的页面",
                sort_order=0,
                status="enabled",
            )
            db.session.add(default_group)
            logger.info("已创建默认分组：默认分组")

        default_tags = [
            {"name": "核心", "color": "red"},
            {"name": "重要", "color": "orange"},
            {"name": "常用", "color": "gold"},
            {"name": "新功能", "color": "green"},
            {"name": "维护中", "color": "default"},
        ]
        for tag_info in default_tags:
            existing = PageTag.query.filter_by(name=tag_info["name"]).first()
            if not existing:
                new_tag = PageTag(
                    name=tag_info["name"],
                    color=tag_info["color"],
                    status="enabled",
                )
                db.session.add(new_tag)
                logger.info("已创建默认标签：%s", tag_info["name"])

        db.session.commit()

        demo_folder = os.path.join(app.config["UPLOAD_ROOT"], "demo-sample")
        os.makedirs(demo_folder, exist_ok=True)
        index_path = os.path.join(demo_folder, "index.html")
        if not os.path.exists(index_path):
            with open(index_path, "w", encoding="utf-8") as file:
                file.write(_demo_page_html())

        demo_page = BusinessPage.query.filter_by(route_path="/pages/demo-sample/index.html").first()
        if not demo_page:
            demo_token = generate_api_token()
            demo_page = BusinessPage(
                name="示例数据看板",
                description="系统自动初始化的示例页面，用于验证上传路由与门户展示链路。",
                category="系统示例",
                developer="System",
                main_page="index.html",
                storage_folder="static/pages/demo-sample",
                route_path="/pages/demo-sample/index.html",
                table_prefix="demo0001",
                table_name="demo0001_records",
                api_token_hash=hash_token(demo_token),
                status="enabled",
                uploader_admin_id=admin.id,
            )
            db.session.add(demo_page)
            db.session.commit()

        if default_group and demo_page not in default_group.pages:
            default_group.pages.append(demo_page)
            db.session.commit()
            logger.info("已将示例页面绑定到默认分组")

        important_tag = PageTag.query.filter_by(name="重要").first()
        if important_tag and demo_page not in important_tag.pages:
            important_tag.pages.append(demo_page)
            db.session.commit()
            logger.info("已为示例页面绑定「重要」标签")

        ensure_dynamic_table(demo_page.table_name)
        try:
            create_record(
                table_name=demo_page.table_name,
                record_key="welcome",
                payload={"message": "示例数据已初始化", "version": "1.0.0"},
            )
        except Exception:
            db.session.rollback()

        logger.info("系统初始化完成")
