"""
Database models for the Schedule App.
"""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_editor = db.Column(db.Boolean, default=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Week(db.Model):
    __tablename__ = "weeks"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)          # e.g. "Next Week: 3/1/26"
    start_date = db.Column(db.Date, nullable=True)
    sort_order = db.Column(db.Integer, default=0)

    rows = db.relationship("Row", backref="week", cascade="all, delete-orphan",
                           order_by="Row.sort_order")


class Column(db.Model):
    __tablename__ = "columns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_default = db.Column(db.Boolean, default=False)


class Row(db.Model):
    __tablename__ = "rows"

    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.Integer, db.ForeignKey("weeks.id"), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    cells = db.relationship("Cell", backref="row", cascade="all, delete-orphan")


class Cell(db.Model):
    __tablename__ = "cells"

    id = db.Column(db.Integer, primary_key=True)
    row_id = db.Column(db.Integer, db.ForeignKey("rows.id"), nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey("columns.id"), nullable=False)
    value = db.Column(db.Text, default="")


class ChangeLog(db.Model):
    __tablename__ = "change_log"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)        # cell_edit, row_added, etc.
    details = db.Column(db.Text, default="")

    user = db.relationship("User")
