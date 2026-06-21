import os

from flask import Flask, jsonify, send_from_directory

from .config import Config
from .database_service import register_db_event_listeners
from .errors import register_error_handlers
from .extensions import db, jwt
from .logging_config import setup_logging
from .routes.admin_pages import bp as admin_pages_bp
from .routes.admin_settings import bp as admin_settings_bp
from .routes.admin_users import bp as admin_users_bp
from .routes.admin_notifications import bp as admin_notifications_bp
from .routes.admin_groups_tags import bp as admin_groups_tags_bp
from .routes.auth import bp as auth_bp
from .routes.data_api import bp as data_api_bp
from .routes.public import bp as public_bp
from .services.bootstrap_service import initialize_defaults


def create_app() -> Flask:
    setup_logging()

    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_ROOT"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)

    register_error_handlers(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_pages_bp)
    app.register_blueprint(admin_settings_bp)
    app.register_blueprint(admin_notifications_bp)
    app.register_blueprint(admin_groups_tags_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(data_api_bp)

    with app.app_context():
        try:
            register_db_event_listeners()
            app.logger.info("数据库事件监听器注册成功")
        except Exception as exc:
            app.logger.warning("注册数据库事件监听器失败：%s", exc)

    @app.before_request
    def _db_health_check_before_request():
        from .database_service import ping_db

        try:
            from flask import request

            if request.method in ("GET", "HEAD"):
                if not ping_db():
                    app.logger.warning("请求前数据库连接异常，已尝试重建会话")
        except Exception:
            pass

    @app.teardown_request
    def _remove_db_session(exc=None):
        if exc is not None:
            from .database_service import is_connection_error

            if is_connection_error(exc):
                app.logger.error(
                    "检测到数据库连接错误，清理会话：%s", exc
                )
                try:
                    db.session.rollback()
                except Exception:
                    pass
        try:
            db.session.remove()
        except Exception:
            pass

    @app.get("/health")
    def health_check():
        return jsonify({"message": "ok"})

    @app.get("/pages/<path:asset_path>")
    def serve_uploaded_pages(asset_path: str):
        return send_from_directory(app.config["UPLOAD_ROOT"], asset_path)

    @app.get("/static/qrcodes/<path:filename>")
    def serve_qrcodes(filename: str):
        qrcode_dir = os.path.join(os.path.dirname(app.config["UPLOAD_ROOT"]), "qrcodes")
        return send_from_directory(qrcode_dir, filename)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    initialize_defaults(app)

    return app
