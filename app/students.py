from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import students as student_model
from services.tracker import compute_balance
from config import DEFAULT_TERM

bp = Blueprint("students", __name__, url_prefix="/students")

@bp.route("/")
def index():
    """List all students with their fee balances."""
    term = DEFAULT_TERM
    all_students = student_model.list_all()
    
    # Calculate balance for each student for the current term
    students_with_balance = []
    for s in all_students:
        try:
            # compute_balance returns a dict with due, paid, balance, arrears
            finance = compute_balance(s["id"], term)
            s["balance"] = finance["balance"]
            s["in_arrears"] = finance["in_arrears"]
            students_with_balance.append(s)
        except ValueError:
            continue

    return render_template("students.html", students=students_with_balance, term=term)


@bp.route("/new", methods=["GET", "POST"])
@bp.route("/<student_id>/edit", methods=["GET", "POST"])
def add_edit(student_id=None):
    """Handle both adding a new student and editing an existing one."""
    editing = student_id is not None

    if editing:
        student = student_model.get(student_id)
        if not student:
            flash(f"Unknown student {student_id}", "error")
            return redirect(url_for("students.index"))

    if request.method == "POST":
        new_id = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        student_class = request.form.get("class", "").strip()
        phone = request.form.get("phone", "").strip()

        errors = []
        if not new_id: errors.append("Student ID is required.")
        if not name: errors.append("Name is required.")
        if not student_class: errors.append("Class is required.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "add_student.html",
                form={"id": new_id, "name": name, "class": student_class, "phone": phone},
                classes=student_model.known_classes(),
                editing=editing,
            )

        try:
            if editing:
                # Keep original ID, just update the rest
                student_model.update(
                    student_id, name=name, student_class=student_class, guardian_phone=phone
                )
                flash(f"Updated {name} ({student_id})", "success")
            else:
                student_model.create(new_id, name, student_class, phone)
                flash(f"Added {name} ({new_id})", "success")
            return redirect(url_for("students.index"))
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "add_student.html",
                form={"id": new_id, "name": name, "class": student_class, "phone": phone},
                classes=student_model.known_classes(),
                editing=editing,
            )

    # GET Request
    if editing:
        form = {
            "id": student_id,
            "name": student["name"],
            "class": student["class"],
            "phone": student.get("guardian_phone", ""),
        }
    else:
        form = {"id": "", "name": "", "class": "", "phone": ""}

    return render_template(
        "add_student.html",
        form=form,
        classes=student_model.known_classes(),
        editing=editing,
    )


@bp.route("/<student_id>/delete", methods=["POST"])
def delete(student_id):
    """Delete a student."""
    student = student_model.get(student_id)
    if not student:
        flash(f"Unknown student {student_id}", "error")
        return redirect(url_for("students.index"))

    try:
        student_model.delete(student_id)
        flash(f"Deleted {student['name']} ({student_id}) and all their records", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("students.index"))