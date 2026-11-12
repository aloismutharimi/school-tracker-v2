from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import students, payments
from models.terms import get_active_term

bp = Blueprint("payments", __name__, url_prefix="/payments")

@bp.route("/new", methods=["GET", "POST"])
def add_payment():
    term = get_active_term()
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

    recent_payments = payments.list_recent_with_names(term)
    return render_template("add_payment.html", students=all_students, form={}, term=term, recent=recent_payments)

@bp.route("/<int:payment_id>/delete", methods=["POST"])
def delete_payment(payment_id):
    try:
        payments.delete(payment_id)
        flash("Payment deleted successfully.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("payments.add_payment"))