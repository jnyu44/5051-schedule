"""
Configuration for the 3-Week Look Ahead Schedule App.
"""
import os

# Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Database — SQLite locally, PostgreSQL on Render
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///schedule.db")
# Render uses postgres:// but SQLAlchemy 1.4+ requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Server
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
