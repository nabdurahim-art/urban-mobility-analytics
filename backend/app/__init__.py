

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS

from config import config_map
from app.routes.trips     import trips_bp
from app.routes.analytics import analytics_bp


def create_app(env: str = "development") -> Flask:

    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["development"]))

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(trips_bp,     url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed on this endpoint"}), 405

    return app