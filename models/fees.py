"""
Fee schedule. Each class has one fee amount per term.
"""
from models.db import get_cursor


def _row_to_dict(row):
    return dict(row) if row else None


def set_fee(student_class, term, amount):
    """
    Insert or update the fee for a class and term.
    If a fee already exists for (class, term), it's replaced.
    """
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO fees (class, term, amount) VALUES (?, ?, ?) "
            "ON CONFLICT(class, term) DO UPDATE SET amount = excluded.amount",
            (student_class, term, float(amount)),
        )

    return get(student_class, term)


def get(student_class, term):
    """Return the fee dict for a class and term, or None."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM fees WHERE class = ? AND term = ?",
            (student_class, term),
        )
        return _row_to_dict(cur.fetchone())


def amount(student_class, term):
    """Return the fee amount as a float. Returns 0.0 if not set."""
    fee = get(student_class, term)
    return float(fee["amount"]) if fee else 0.0


def list_all(term=None):
    """Return all fees, optionally filtered to one term."""
    with get_cursor() as cur:
        if term:
            cur.execute(
                "SELECT * FROM fees WHERE term = ? ORDER BY class",
                (term,),
            )
        else:
            cur.execute("SELECT * FROM fees ORDER BY term, class")
        return [dict(row) for row in cur.fetchall()]


def delete(student_class, term):
    """Remove a fee entry. Returns the deleted record."""
    fee = get(student_class, term)
    if not fee:
        raise ValueError(f"No fee for {student_class} in {term}")

    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM fees WHERE class = ? AND term = ?",
            (student_class, term),
        )

    return fee