"""
Business logic for tracking balances, arrears, and performance.
Uses the models layer for data access.
"""
from models import students, payments, scores, fees
from config import DEFAULT_TERM


def compute_balance(student_id, term=None):
    """
    Calculate the financial status for one student.
    Returns a dict with due, paid, balance, and arrears status.
    """
    term = term or DEFAULT_TERM
    
    student = students.get(student_id)
    if not student:
        raise ValueError(f"Unknown student {student_id}")

    # Get fee due for their class
    fee_due = fees.amount(student["class"], term)
    
    # Get total paid by this student in this term
    total_paid = payments.total_for_student(student_id, term)
    
    balance = fee_due - total_paid
    
    return {
        "student_id": student["id"],
        "name": student["name"],
        "class": student["class"],
        "term": term,
        "due": fee_due,
        "paid": total_paid,
        "balance": balance,
        "in_arrears": total_paid < fee_due,
    }


def build_finance_data(term=None):
    """
    Return financial data for all students.
    Useful for the dashboard and full reports.
    """
    term = term or DEFAULT_TERM
    all_students = students.list_all()
    
    # Calculate balance for each student
    finance_rows = []
    for s in all_students:
        try:
            finance_rows.append(compute_balance(s["id"], term))
        except ValueError:
            continue
            
    # Sort by balance descending (highest arrears first)
    finance_rows.sort(key=lambda x: x["balance"], reverse=True)
    return finance_rows


def build_performance_data(term=None, target_class=None):
    """
    Calculate average scores and rank students within their class.
    If target_class is provided, only rank that class.
    """
    term = term or DEFAULT_TERM
    all_students = students.list_all()
    
    if target_class:
        all_students = [s for s in all_students if s["class"] == target_class]

    perf_rows = []
    for s in all_students:
        avg = scores.average_for_student(s["id"], term)
        if avg is not None:
            perf_rows.append({
                "student_id": s["id"],
                "name": s["name"],
                "class": s["class"],
                "average": avg
            })
            
    # Group by class to calculate ranks
    classes = set(r["class"] for r in perf_rows)
    for c in classes:
        # Get all students in this class, sort by average descending
        class_rows = [r for r in perf_rows if r["class"] == c]
        class_rows.sort(key=lambda x: x["average"], reverse=True)
        
        # Assign rank
        current_rank = 1
        for i, row in enumerate(class_rows):
            # Handle ties (if average is same as previous, keep same rank)
            if i > 0 and row["average"] == class_rows[i-1]["average"]:
                row["rank"] = class_rows[i-1]["rank"]
            else:
                row["rank"] = current_rank
            current_rank += 1

    # Sort the final list by class, then rank
    perf_rows.sort(key=lambda x: (x["class"], x["rank"]))
    return perf_rows


def get_class_summary(term=None):
    """
    Calculate school-wide and per-class summaries.
    Returns a dict with totals and top performers.
    """
    term = term or DEFAULT_TERM
    
    finance_data = build_finance_data(term)
    perf_data = build_performance_data(term)
    
    # --- School Totals ---
    total_billed = sum(r["due"] for r in finance_data)
    total_collected = sum(r["paid"] for r in finance_data)
    total_outstanding = total_billed - total_collected
    arrears_count = sum(1 for r in finance_data if r["in_arrears"])
    
    # --- Overall Top Performer ---
    top_performer = None
    if perf_data:
        # Since perf_data is sorted by class then rank, the top performer
        # is the one with the highest average overall.
        top_performer = max(perf_data, key=lambda x: x["average"])
    
    # --- Per-Class Breakdown ---
    classes_data = {}
    for s in students.list_all():
        c_name = s["class"]
        if c_name not in classes_data:
            classes_data[c_name] = {
                "name": c_name,
                "student_count": 0,
                "billed": 0,
                "collected": 0,
                "outstanding": 0,
                "arrears": 0,
                "average": 0,
                "top_performer": None,
            }
            
    # Fill class financials
    for row in finance_data:
        c = row["class"]
        classes_data[c]["student_count"] += 1
        classes_data[c]["billed"] += row["due"]
        classes_data[c]["collected"] += row["paid"]
        classes_data[c]["outstanding"] += row["balance"]
        if row["in_arrears"]:
            classes_data[c]["arrears"] += 1
            
    # Fill class performance
    for row in perf_data:
        c = row["class"]
        if row["rank"] == 1 and not classes_data[c]["top_performer"]:
            classes_data[c]["top_performer"] = {
                "name": row["name"],
                "average": round(row["average"], 1)
            }
            
    # Calculate class averages
    for c, data in classes_data.items():
        class_scores = [r["average"] for r in perf_data if r["class"] == c]
        if class_scores:
            data["average"] = round(sum(class_scores) / len(class_scores), 1)

    # Return a sorted list of classes
    sorted_classes = [classes_data[k] for k in sorted(classes_data.keys())]

    return {
        "total_students": len(finance_data),
        "total_billed": total_billed,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
        "arrears_count": arrears_count,
        "top_performer": top_performer,
        "classes": sorted_classes,
    }