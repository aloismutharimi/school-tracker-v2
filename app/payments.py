from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import students, payments
from config import DEFAULT_TERM

bp = Blueprint("payments", __name__, url_prefix="/payments")

@bp.route("/new", methods=["GET", "POST"])
def add_payment():
    term = DEFAULT_TERM
    # Sort students by class, then name for the dropdown
    all_students = sorted(students.list_all(), key=lambda s: (s["class"], s["name"]))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        amount = request.form.get("amount", "").strip()
        method = request.form.get("method", "cash").strip()
        date = request.form.get("date", "").strip() or None

        errors = []
        if not student_id: errors.append("Please select a student.")
        if not amount: errors.append("Amount is required.")
        else:
            try:
                if float(amount) <= 0: errors.append("Amount must be greater than zero.")
            except ValueError:
                errors.append("Amount must be a number.")

        if errors:
            for e in errors: flash(e, "error")
            return render_template("add_payment.html", students=all_students, form=request.form, term=term)

        try:
            payments.create(student_id, term, float(amount), method, date)
            student = students.get(student_id)
            flash(f"Recorded {float(amount):,.0f} from {student['name']}", "success")
            return redirect(url_for("payments.add_payment"))
        except Exception as e:
            flash(str(e), "error")
            return render_template("add_payment.html", students=all_students, form=request.form, term=term)

    return render_template("add_payment.html", students=all_students, form={}, term=term)