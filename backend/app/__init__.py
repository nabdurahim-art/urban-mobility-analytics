"""Flask application factory for the Urban Mobility Analytics API."""

from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

from config import config_map


def create_app(environment="development"):
    """Create and configure the API application."""
    app = Flask(__name__)
    app.config.from_object(config_map.get(environment, config_map["development"]))
    CORS(app)

    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    @app.get("/")
    def dashboard():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:filename>")
    def frontend_asset(filename):
        return send_from_directory(frontend_dir, filename)

    from app.api import api

    app.register_blueprint(api)
    return app
