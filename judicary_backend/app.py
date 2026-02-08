"""
Judiciary System Backend – Flask Application
=============================================
Provides REST API for case management, web scraping of Pakistani court data,
user authentication, search, and analytics.
"""

import logging
import os
import sys

# Ensure the backend package directory is on sys.path
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_mongoengine import MongoEngine

from config import get_config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory."""
    app = Flask(__name__)

    # Load configuration
    cfg = get_config()
    app.config.from_object(cfg)

    # Initialize extensions
    db = MongoEngine()
    db.init_app(app)
    logger.info("MongoDB configured (lazy connect): %s", cfg.MONGODB_URL[:50] + "...")

    CORS(app, origins=cfg.CORS_ORIGINS, supports_credentials=True)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.case_routes import case_bp
    from routes.scraper_routes import scraper_bp
    from routes.search_routes import search_bp
    from routes.analytics_routes import analytics_bp
    from routes.ai_routes import ai_bp
    from routes.document_routes import document_bp
    from routes.translation_routes import translation_bp
    from routes.template_routes import template_bp
    from routes.lawyer_routes import lawyer_bp
    from routes.notification_routes import notification_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(case_bp, url_prefix="/api")
    app.register_blueprint(scraper_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(document_bp, url_prefix="/api")
    app.register_blueprint(translation_bp, url_prefix="/api")
    app.register_blueprint(template_bp, url_prefix="/api")
    app.register_blueprint(lawyer_bp, url_prefix="/api")
    app.register_blueprint(notification_bp, url_prefix="/api")

    # Initialize scraper scheduler
    from routes.scraper_routes import init_scheduler

    sched = init_scheduler(
        app_config={
            "user_agent": cfg.SCRAPER_USER_AGENT,
            "request_delay": cfg.SCRAPER_REQUEST_DELAY,
            "max_pages": cfg.SCRAPER_MAX_PAGES,
        }
    )
    # Only start scheduled jobs if not in testing
    if os.getenv("FLASK_ENV") != "testing":
        sched.start()
        logger.info("Scraper scheduler started")

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "judiciary-backend"}), 200

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    logger.info("Judiciary Backend initialized successfully")
    return app


# Ensure CWD is the backend directory so relative imports work
# when app.py is invoked via absolute path from any directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port, use_reloader=False)
