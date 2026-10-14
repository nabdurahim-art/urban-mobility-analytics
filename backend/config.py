import os
from dotenv import load_dotenv

load_dotenv(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 26257))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_SSL_MODE = "require"

    DEBUG = False
    TESTING = False
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 500

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}            