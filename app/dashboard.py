from flask import Blueprint, render_template
from services.tracker import get_class_summary
from config import DEFAULT_TERM

bp = Blueprint("dashboard", __name__)

@bp.route("/")
def home():
    term = DEFAULT_TERM
    # Call the new v2 service layer!
    data = get_class_summary(term)
    
    return render_template(
        "dashboard.html", 
        term=term, 
        **data
    )