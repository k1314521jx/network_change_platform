import logging
import os
import traceback
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import SQLALCHEMY_DATABASE_URI, FLASK_HOST, FLASK_PORT, FLASK_DEBUG, UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from models import db


def post_fork(server, worker):
    """gunicorn worker fork 后重建数据库连接池，避免 preload 导致的连接共享问题"""
    with server.app.app_context():
        db.engine.dispose()


def _setup_flask_logging(app):
    """配置 Flask 日志：RotatingFileHandler 50MB 分割 + 3 备份，与 Celery 日志分开存储"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "flask.log"),
        maxBytes=50 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.propagate = False

    # Werkzeug 访问日志也写入 flask.log
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(console_handler)
    werkzeug_logger.propagate = False


def create_app():
    app = Flask(
        __name__,
        static_folder="frontend/dist",
        static_url_path=None,
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 3600
    app.config["SQLALCHEMY_POOL_PRE_PING"] = True
    app.config["SECRET_KEY"] = "network-change-platform-secret"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    _setup_flask_logging(app)

    CORS(app)
    db.init_app(app)

    # 全局异常捕获：记录详细 traceback
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        tb = traceback.format_exc()
        app.logger.error(f"[全局异常] {type(e).__name__}: {e}\n{tb}")
        return jsonify({"code": 500, "msg": "服务器内部错误", "data": None}), 500

    # Ensure upload folder
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Register blueprints
    from api.rule_api import rule_bp
    from api.triple_api import triple_bp
    from api.review_api import review_bp
    from api.neo4j_api import neo4j_bp
    from api.ai_review_api import ai_review_bp
    from api.prompt_api import prompt_bp
    from api.model_api import model_bp
    from api.rule_validation_api import rule_validation_bp
    from api.graph_api import graph_bp

    app.register_blueprint(rule_bp)
    app.register_blueprint(triple_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(neo4j_bp)
    app.register_blueprint(ai_review_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(rule_validation_bp)
    app.register_blueprint(graph_bp)

    # SPA catch-all: serve Vue's index.html for any non-API route
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    # Create tables + seed builtin prompts
    with app.app_context():
        db.create_all()
        from services.prompt_service import seed_builtin_prompts
        seed_builtin_prompts()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
