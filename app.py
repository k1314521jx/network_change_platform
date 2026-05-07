import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import SQLALCHEMY_DATABASE_URI, FLASK_HOST, FLASK_PORT, FLASK_DEBUG, UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from models import db


def create_app():
    app = Flask(
        __name__,
        static_folder="frontend/dist",
        static_url_path="",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "network-change-platform-secret"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    CORS(app)
    db.init_app(app)

    # Ensure upload folder
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Register blueprints
    from api.rule_api import rule_bp
    from api.triple_api import triple_bp
    from api.review_api import review_bp
    from api.neo4j_api import neo4j_bp
    from api.ai_review_api import ai_review_bp

    app.register_blueprint(rule_bp)
    app.register_blueprint(triple_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(neo4j_bp)
    app.register_blueprint(ai_review_bp)

    # SPA catch-all: serve Vue's index.html for any non-API route
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    # Create tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
