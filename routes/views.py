"""
Main page views.
"""
from flask import Blueprint, render_template, session

from models import db, Week, Column as Col

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def schedule():
    """Render the schedule grid page."""
    weeks = Week.query.order_by(Week.sort_order).all()
    columns = Col.query.order_by(Col.sort_order).all()

    is_editor = session.get("is_editor", False)
    user_name = session.get("user_name", None)

    return render_template(
        "schedule.html",
        weeks=weeks,
        columns=columns,
        is_editor=is_editor,
        user_name=user_name,
    )
