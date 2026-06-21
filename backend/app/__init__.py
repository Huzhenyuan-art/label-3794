import os

from flask import Flask, jsonify, send_from_directory

from .config import Config
from .errors import register_error_handlers
from .extensions import db, jwt
from .logging_config import setup_logging
from .routes.admin_pages import bp as admin_pages_bp
from .routes.admin_settings import bp as admin_settings_bp
from .routes.admin_users import bp as admin_users_bp
from .routes.admin_notifications import bp as admin_notifications_bp
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
    app.register_blueprint(public_bp)
    app.register_blueprint(data_api_bp)

    @app.get("/health")
    def health_check():
        return jsonify({"message": "ok"})

    @app.get("/pages/<path:asset_path>")
    def serve_uploaded_pages(asset_path: str):
        return send_from_directory(app.config["UPLOAD_ROOT"], asset_path)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    initialize_defaults(app)

    return app
