from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.tracker import get_class_summary
from models.terms import set_active_term, get_active_term, create_term

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