"""
JSON API endpoints for the schedule grid.
Called by the frontend JS to read/create/update/delete rows and cells.
"""
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, session

from models import db, Week, Column as Col, Row, Cell, ChangeLog

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _log_change(action: str, details: str) -> None:
    """Record a change in the change_log table."""
    entry = ChangeLog(
        timestamp=datetime.now(timezone.utc),
        user_id=session.get("user_id"),
        action=action,
        details=details,
    )
    db.session.add(entry)


def _require_editor():
    """Return a 403 response if the current user is not an editor."""
    if not session.get("is_editor"):
        return jsonify({"error": "Not authorized"}), 403
    return None


# ── READ ─────────────────────────────────────────────────────────────
@api_bp.route("/schedule")
def get_schedule():
    """Return the full schedule as JSON."""
    weeks = Week.query.order_by(Week.sort_order).all()
    columns = Col.query.order_by(Col.sort_order).all()

    col_list = [{"id": c.id, "name": c.name, "is_default": c.is_default} for c in columns]

    week_list = []
    for w in weeks:
        rows = []
        for r in w.rows:
            cell_map = {}
            for cell in r.cells:
                cell_map[str(cell.column_id)] = cell.value
            rows.append({"id": r.id, "sort_order": r.sort_order, "cells": cell_map})
        week_list.append({
            "id": w.id,
            "label": w.label,
            "start_date": w.start_date.isoformat() if w.start_date else None,
            "sort_order": w.sort_order,
            "rows": rows,
        })

    return jsonify({"columns": col_list, "weeks": week_list})


# ── CELL EDIT ────────────────────────────────────────────────────────
@api_bp.route("/cell", methods=["PUT"])
def update_cell():
    """Update a single cell value."""
    err = _require_editor()
    if err:
        return err

    data = request.get_json()
    row_id = data.get("row_id")
    column_id = data.get("column_id")
    value = data.get("value", "")

    cell = Cell.query.filter_by(row_id=row_id, column_id=column_id).first()
    if not cell:
        cell = Cell(row_id=row_id, column_id=column_id, value=value)
        db.session.add(cell)
    else:
        old_value = cell.value
        cell.value = value

    col = Col.query.get(column_id)
    col_name = col.name if col else "?"
    _log_change("cell_edit", f"Row {row_id}, {col_name}: '{old_value if cell.id else ''}' → '{value}'")

    db.session.commit()
    return jsonify({"ok": True})


# ── ROW INSERT ───────────────────────────────────────────────────────
@api_bp.route("/row", methods=["POST"])
def add_row():
    """Add a new row to a week."""
    err = _require_editor()
    if err:
        return err

    data = request.get_json()
    week_id = data.get("week_id")
    after_sort = data.get("after_sort", 0)

    # Shift rows below the insertion point
    rows_below = Row.query.filter(
        Row.week_id == week_id, Row.sort_order > after_sort
    ).all()
    for r in rows_below:
        r.sort_order += 1

    new_row = Row(week_id=week_id, sort_order=after_sort + 1)
    db.session.add(new_row)
    db.session.flush()  # get new_row.id

    # Create empty cells for all columns
    columns = Col.query.all()
    for col in columns:
        db.session.add(Cell(row_id=new_row.id, column_id=col.id, value=""))

    week = Week.query.get(week_id)
    _log_change("row_added", f"New row in '{week.label}' at position {after_sort + 1}")

    db.session.commit()
    return jsonify({"ok": True, "row_id": new_row.id})


# ── ROW DELETE ───────────────────────────────────────────────────────
@api_bp.route("/row/<int:row_id>", methods=["DELETE"])
def delete_row(row_id):
    """Delete a row and its cells."""
    err = _require_editor()
    if err:
        return err

    row = Row.query.get(row_id)
    if not row:
        return jsonify({"error": "Row not found"}), 404

    week = Week.query.get(row.week_id)
    # Summarize what's being deleted
    first_cell = Cell.query.filter_by(row_id=row_id).first()
    summary = first_cell.value if first_cell else "(empty)"
    _log_change("row_deleted", f"Deleted row '{summary}' from '{week.label}'")

    db.session.delete(row)
    db.session.commit()
    return jsonify({"ok": True})


# ── WEEK MANAGEMENT ────────────────────────────────────────────────
@api_bp.route("/week", methods=["POST"])
def add_week():
    """Add a new week section."""
    err = _require_editor()
    if err:
        return err

    data = request.get_json()
    label = data.get("label", "New Week")
    start_date_str = data.get("start_date")

    from datetime import date
    start_date = None
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            pass

    max_order = db.session.query(db.func.max(Week.sort_order)).scalar() or 0
    week = Week(label=label, start_date=start_date, sort_order=max_order + 1)
    db.session.add(week)
    _log_change("week_added", f"New week: '{label}'")
    db.session.commit()
    return jsonify({"ok": True, "week_id": week.id})


# ── COLUMN MANAGEMENT ──────────────────────────────────────────────
@api_bp.route("/column", methods=["POST"])
def add_column():
    """Add a custom column."""
    err = _require_editor()
    if err:
        return err

    data = request.get_json()
    name = data.get("name", "New Column")

    max_order = db.session.query(db.func.max(Col.sort_order)).scalar() or 0
    col = Col(name=name, sort_order=max_order + 1, is_default=False)
    db.session.add(col)
    db.session.flush()

    # Add empty cells for every existing row
    rows = Row.query.all()
    for r in rows:
        db.session.add(Cell(row_id=r.id, column_id=col.id, value=""))

    _log_change("column_added", f"New column: '{name}'")
    db.session.commit()
    return jsonify({"ok": True, "column_id": col.id})


# ── CHANGE LOG ──────────────────────────────────────────────────────
@api_bp.route("/changelog")
def get_changelog():
    """Return the last 100 changes."""
    entries = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).limit(100).all()
    return jsonify({
        "entries": [
            {
                "timestamp": e.timestamp.isoformat(),
                "user": e.user.name if e.user else "Unknown",
                "action": e.action,
                "details": e.details,
            }
            for e in entries
        ]
    })
