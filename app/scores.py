from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import students, scores
from config import DEFAULT_TERM

bp = Blueprint("scores", __name__, url_prefix="/scores")

@bp.route("/new", methods=["GET", "POST"])
def add_score():
    term = DEFAULT_TERM
    all_students = sorted(students.list_all(), key=lambda s: (s["class"], s["name"]))
    subjects = ["Mathematics", "English", "Kiswahili", "Science", "Social Studies", "CRE"]

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        subject = request.form.get("subject", "").strip()
        score = request.form.get("score", "").strip()

        errors = []
        if not student_id: errors.append("Please select a student.")
        if not subject: errors.append("Subject is required.")
        if not score: errors.append("Score is required.")
        else:
            try:
                if float(score) < 0 or float(score) > 100:
                    errors.append("Score must be between 0 and 100.")
            except ValueError:
                errors.append("Score must be a number.")

        if errors:
            for e in errors: flash(e, "error")
            return render_template("add_score.html", students=all_students, subjects=subjects, form=request.form, term=term)

        try:
            scores.create(student_id, term, subject, float(score))
            student = students.get(student_id)
            flash(f"Recorded {subject} {float(score):.0f} for {student['name']}", "success")
            return redirect(url_for("scores.add_score"))
        except Exception as e:
            flash(str(e), "error")
            return render_template("add_score.html", students=all_students, subjects=subjects, form=request.form, term=term)

    return render_template("add_score.html", students=all_students, subjects=subjects, form={}, term=term)