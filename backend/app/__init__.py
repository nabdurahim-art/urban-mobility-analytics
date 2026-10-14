"""Flask application factory for Urban Mobility Analytics."""

from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import config_map


def create_app(env="development"):
    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["development"]))
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    @app.get("/")
    def dashboard():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:filename>")
    def frontend_asset(filename):
        return send_from_directory(frontend_dir, filename)

    from app.routes.analytics import analytics_bp
    from app.routes.trips import trips_bp

    app.register_blueprint(trips_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed on this endpoint"}), 405

    return app
