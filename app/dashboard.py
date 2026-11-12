import os
from flask import Blueprint, render_template, request, redirect, url_for, flash,  send_file
from services.tracker import get_class_summary
from models.terms import set_active_term, get_active_term, create_term
from config import DB_PATH
from datetime import datetime

bp = Blueprint("dashboard", __name__)

@bp.route("/")
def home():
    # 1. Get the active term from the DB
    active_term = get_active_term()
    
    # 2. Pass it to the service layer so it filters the data!
    data = get_class_summary(active_term)
    
    # 3. Return the template (current_term is handled globally, but we can pass active_term if the template uses 'term')
    return render_template("dashboard.html", **data)

@bp.route("/switch-term", methods=["POST"])
def switch_term():
    term_input = request.form.get("term", "").strip()
    action = request.form.get("action", "switch") # 'switch' or 'create'
    
    if term_input:
        if action == "create":
            create_term(term_input)
            set_active_term(term_input)
            flash(f"Created and switched to {term_input}", "success")
        else:
            set_active_term(term_input)
            flash(f"Switched to {term_input}", "success")
            
    return redirect(request.referrer or url_for("dashboard.home"))

@bp.route("/backup")
def backup():
    """Download a copy of the SQLite database."""
    if not os.path.exists(DB_PATH):
        flash("Database file not found.", "error")
        return redirect(url_for("dashboard.home"))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"school_tracker_backup_{timestamp}.db"    
    return send_file(
        DB_PATH,
        as_attachment=True,
        download_name=filename,
        mimetype="application/x-sqlite3"
    )