"""
Fee payments made by students.
"""
from datetime import date, datetime

from models.db import get_cursor


def _row_to_dict(row):
    return dict(row) if row else None


def create(student_id, term, amount, method="cash", payment_date=None):
    """Record a payment."""
    now = datetime.now().isoformat(timespec="seconds")
    payment_date = payment_date or date.today().isoformat()

    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO payments (student_id, term, amount, method, date, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, term, float(amount), method, payment_date, now),
        )
        payment_id = cur.lastrowid

    return get(payment_id)


def get(payment_id):
    """Return one payment by its internal ID."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        return _row_to_dict(cur.fetchone())


def list_all(term=None):
    """Return all payments, newest first."""
    with get_cursor() as cur:
        if term:
            cur.execute(
                "SELECT * FROM payments WHERE term = ? ORDER BY id DESC",
                (term,),
            )
        else:
            cur.execute("SELECT * FROM payments ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]


def list_by_student(student_id, term=None):
    """Return all payments for one student, newest first."""
    with get_cursor() as cur:
        if term:
            cur.execute(
                "SELECT * FROM payments WHERE student_id = ? AND term = ? "
                "ORDER BY id DESC",
                (student_id, term),
            )
        else:
            cur.execute(
                "SELECT * FROM payments WHERE student_id = ? ORDER BY id DESC",
                (student_id,),
            )
        return [dict(row) for row in cur.fetchall()]


def total_for_student(student_id, term):
    """Return the total amount paid by a student in a term."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM payments "
            "WHERE student_id = ? AND term = ?",
            (student_id, term),
        )
        return float(cur.fetchone()["total"])


def total_for_term(term):
    """Return the total collected across all students in a term."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE term = ?",
            (term,),
        )
        return float(cur.fetchone()["total"])


def update(payment_id, amount=None, method=None, payment_date=None):
    """Update a payment's amount, method, or date."""
    payment = get(payment_id)
    if not payment:
        raise ValueError(f"Unknown payment {payment_id}")

    new_amount = float(amount) if amount is not None else payment["amount"]
    new_method = method if method is not None else payment["method"]
    new_date = payment_date if payment_date is not None else payment["date"]

    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE payments SET amount = ?, method = ?, date = ? WHERE id = ?",
            (new_amount, new_method, new_date, payment_id),
        )

    return get(payment_id)


def delete(payment_id):
    """Delete a payment. Returns the deleted record."""
    payment = get(payment_id)
    if not payment:
        raise ValueError(f"Unknown payment {payment_id}")

    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM payments WHERE id = ?", (payment_id,))

    return payment