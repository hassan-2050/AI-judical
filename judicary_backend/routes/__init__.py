from routes.auth_routes import auth_bp
from routes.case_routes import case_bp
from routes.scraper_routes import scraper_bp
from routes.search_routes import search_bp
from routes.analytics_routes import analytics_bp

__all__ = ["auth_bp", "case_bp", "scraper_bp", "search_bp", "analytics_bp"]
