"""
Authentication routes — login / logout.
"""
from flask import Blueprint, request, redirect, url_for, render_template, session, flash

from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_editor"] = user.is_editor
            return redirect(url_for("views.schedule"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("views.schedule"))
