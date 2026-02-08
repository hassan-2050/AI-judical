import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

    # MongoDB
    MONGODB_URL = os.getenv(
        "MONGODB_URL", "mongodb://localhost:27017/judiciary_system"
    )
    MONGODB_SETTINGS = {
        "host": MONGODB_URL,
        "connect": False,
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 10000,
    }

    # Scraper settings
    SCRAPER_USER_AGENT = os.getenv(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    SCRAPER_REQUEST_DELAY = int(os.getenv("SCRAPER_REQUEST_DELAY", "2"))
    SCRAPER_MAX_PAGES = int(os.getenv("SCRAPER_MAX_PAGES", "50"))

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002").split(",")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
