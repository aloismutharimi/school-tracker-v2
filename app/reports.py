from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import os

from models import students
from services.tracker import build_finance_data, build_performance_data
from services.pdf_report import export_full_pdf, export_student_pdf
from config import DEFAULT_TERM, DATA_DIR

bp = Blueprint("reports", __name__, url_prefix="/reports")

@bp.route("/", methods=["GET", "POST"])
def index():
    term = DEFAULT_TERM
    all_students = sorted(students.list_all(), key=lambda s: (s["class"], s["name"]))
    classes = sorted({s["class"] for s in all_students})

    form = {"mode": "full", "class_filter": "", "student_id": ""}
    report_data = None

    if request.method == "POST":
        form["mode"] = request.form.get("mode", "full")
        form["class_filter"] = request.form.get("class_filter", "").strip()
        form["student_id"] = request.form.get("student_id", "").strip()

        # Determine which students match the filter
        if form["student_id"]:
            target_students = [s for s in all_students if s["id"] == form["student_id"]]
        elif form["class_filter"]:
            target_students = [s for s in all_students if s["class"] == form["class_filter"]]
        else:
            target_students = all_students

        if not target_students:
            flash("No students match the given filters.", "error")
        else:
            # Build the data for the HTML view
            finance_data = build_finance_data(term) if form["mode"] in ("fees", "full") else []
            perf_data = build_performance_data(term, form["class_filter"] or None) if form["mode"] in ("grades", "full") else []

            # If a solo student is selected, filter the view down to just them
            if form["student_id"]:
                finance_data = [r for r in finance_data if r["student_id"] == form["student_id"]]
                perf_data = [r for r in perf_data if r["student_id"] == form["student_id"]]

            report_data = {
                "title": form["student_id"] or form["class_filter"] or "Full School Report",
                "is_solo": bool(form["student_id"]),
                "finance": finance_data,
                "performance": perf_data,
            }

    return render_template(
        "reports.html",
        term=term,
        classes=classes,
        students=all_students,
        form=form,
        report=report_data
    )


@bp.route("/download")
def download():
    term = DEFAULT_TERM
    fmt = request.args.get("format", "pdf").lower()
    student_id = request.args.get("student", "").strip() or None

    try:
        if student_id:
            # Generate Solo PDF
            path = export_student_pdf(student_id, term)
        else:
            # Generate Full School PDF (You can expand this to support class filters later)
            path = export_full_pdf(term)
            
        if not os.path.exists(path):
            flash("File could not be generated.", "error")
            return redirect(url_for("reports.index"))
            
        return send_file(
            path, 
            as_attachment=True, 
            download_name=os.path.basename(path),
            mimetype="application/pdf"
        )
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("reports.index"))