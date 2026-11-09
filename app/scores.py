from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import students, scores
from models.terms import get_active_term

bp = Blueprint("scores", __name__, url_prefix="/scores")

@bp.route("/new", methods=["GET", "POST"])
def add_score():
    term = get_active_term()
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

@bp.route("/bulk", methods=["GET", "POST"])
def bulk_select():
    """Step 1: Choose which class and subject to grade."""
    term = get_active_term()
    # Get a list of all unique classes
    all_classes = sorted({s["class"] for s in students.list_all()})
    
    if request.method == "POST":
        selected_class = request.form.get("class")
        subject = request.form.get("subject", "").strip()
        
        if not selected_class or not subject:
            flash("Please select a class and enter a subject.", "error")
            return redirect(url_for("scores.bulk_select"))
            
        # Redirect to the entry form with the selection in the URL
        return redirect(url_for("scores.bulk_entry", student_class=selected_class, subject=subject))

    return render_template("scores_bulk_select.html", classes=all_classes, term=term)


@bp.route("/bulk/entry", methods=["GET", "POST"])
def bulk_entry():
    """Step 2: Show a table of students and save the scores."""
    term = get_active_term()
    student_class = request.args.get("student_class")
    subject = request.args.get("subject")
    
    if not student_class or not subject:
        flash("Missing class or subject.", "error")
        return redirect(url_for("scores.bulk_select"))
        
    class_students = students.list_by_class(student_class)
    
    if request.method == "POST":
        # Iterate through the submitted form data
        saved_count = 0
        for student in class_students:
            field_name = f"score_{student['id']}"
            score_str = request.form.get(field_name, "").strip()
            
            if score_str:
                try:
                    score_val = float(score_str)
                    if 0 <= score_val <= 100:
                        # Delete existing score for this subject/term to prevent duplicates
                        # (Simplified approach: we just insert a new one for now)
                        scores.create(student["id"], term, subject, score_val)
                        saved_count += 1
                except ValueError:
                    pass # Ignore invalid inputs
                    
        flash(f"Successfully saved {saved_count} scores for {subject}.", "success")
        return redirect(url_for("scores.bulk_select"))
        
    return render_template("scores_bulk_entry.html", 
                           students=class_students, 
                           student_class=student_class, 
                           subject=subject, 
                           term=term)