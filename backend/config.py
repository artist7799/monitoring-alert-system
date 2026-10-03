import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-flask-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-secret-change-later")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")))

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "monitoring_alert_system")
    
    # Priority: 1. DATABASE_URL env 2. SQLite if DB_TYPE=sqlite or DB_PASSWORD empty and mysql unavailable 3. MySQL
    if os.getenv("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    elif os.getenv("DB_TYPE") == "sqlite" or os.getenv("USE_SQLITE", "false").lower() == "true":
        SQLALCHEMY_DATABASE_URI = "sqlite:///monitoring.db"
    else:
        encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
