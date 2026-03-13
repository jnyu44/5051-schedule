"""
3-Week Look Ahead Schedule App — Flask entry point.

Creates the Flask app, registers blueprints, initializes the database,
and seeds the 3 editor accounts on first run.
"""
from flask import Flask, g

from config import SECRET_KEY, DATABASE_URL, HOST, PORT, DEBUG
from models import db, User, Column as Col
from routes.auth import auth_bp
from routes.views import views_bp
from routes.api import api_bp

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {"connect_timeout": 10} if "postgresql" in DATABASE_URL else {},
}

db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(views_bp)
app.register_blueprint(api_bp)


# ---------------------------------------------------------------------------
# Database initialization + seed data
# ---------------------------------------------------------------------------
DEFAULT_COLUMNS = [
    "Contractor",
    "Date",
    "Task",
    "Activities",
    "Confirmed",
    "Pending",
]

SEED_USERS = [
    {"name": "Edwin Tsay", "email": "edwin.tsay@pondviewseattle.com"},
    {"name": "Emilio", "email": "emilio@greencanopynode.com"},
    {"name": "Justin", "email": "justin@greencanopynode.com"},
]

DEFAULT_PASSWORD = "team5051"

_db_initialized = False


def seed_database():
    """Create default columns and editor accounts if they don't exist."""
    # Seed columns
    if Col.query.count() == 0:
        for i, name in enumerate(DEFAULT_COLUMNS):
            db.session.add(Col(name=name, sort_order=i, is_default=True))
        db.session.commit()

    # Seed users
    for u in SEED_USERS:
        if not User.query.filter_by(email=u["email"]).first():
            user = User(name=u["name"], email=u["email"], is_editor=True)
            user.set_password(DEFAULT_PASSWORD)
            db.session.add(user)
    db.session.commit()


@app.before_request
def init_db():
    """Initialize the database on the first request (not at import time)."""
    global _db_initialized
    if not _db_initialized:
        db.create_all()
        seed_database()
        _db_initialized = True


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)

