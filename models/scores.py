"""
Exam scores per student, per subject, per term.
"""
from datetime import datetime

from models.db import get_cursor


def _row_to_dict(row):
    return dict(row) if row else None


def create(student_id, term, subject, score, out_of=100):
    """Record an exam score."""
    now = datetime.now().isoformat(timespec="seconds")

    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO scores (student_id, term, subject, score, out_of, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, term, subject, float(score), float(out_of), now),
        )
        score_id = cur.lastrowid

    return get(score_id)


def get(score_id):
    """Return one score by its internal ID."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM scores WHERE id = ?", (score_id,))
        return _row_to_dict(cur.fetchone())


def list_all(term=None):
    """Return all scores, newest first."""
    with get_cursor() as cur:
        if term:
            cur.execute(
                "SELECT * FROM scores WHERE term = ? ORDER BY id DESC",
                (term,),
            )
        else:
            cur.execute("SELECT * FROM scores ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]


def list_by_student(student_id, term=None):
    """Return all scores for a student."""
    with get_cursor() as cur:
        if term:
            cur.execute(
                "SELECT * FROM scores WHERE student_id = ? AND term = ? "
                "ORDER BY subject",
                (student_id, term),
            )
        else:
            cur.execute(
                "SELECT * FROM scores WHERE student_id = ? ORDER BY term, subject",
                (student_id,),
            )
        return [dict(row) for row in cur.fetchall()]


def list_by_term(term):
    """Return all scores for a term."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM scores WHERE term = ?", (term,))
        return [dict(row) for row in cur.fetchall()]


def list_by_class_and_term(student_class, term):
    """
    Return all scores for students in one class in one term.
    Joins to students to filter by class.
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT s.* FROM scores s "
            "JOIN students st ON st.id = s.student_id "
            "WHERE st.class = ? AND s.term = ?",
            (student_class, term),
        )
        return [dict(row) for row in cur.fetchall()]


def average_for_student(student_id, term):
    """Return a student's average percentage for a term, or None if no scores."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT AVG(score * 100.0 / out_of) AS avg FROM scores "
            "WHERE student_id = ? AND term = ?",
            (student_id, term),
        )
        row = cur.fetchone()
        return round(float(row["avg"]), 2) if row["avg"] is not None else None


def update(score_id, subject=None, score=None, out_of=None):
    """Update a score's subject, value, or out_of."""
    existing = get(score_id)
    if not existing:
        raise ValueError(f"Unknown score {score_id}")

    new_subject = subject if subject is not None else existing["subject"]
    new_score = float(score) if score is not None else existing["score"]
    new_out_of = float(out_of) if out_of is not None else existing["out_of"]

    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE scores SET subject = ?, score = ?, out_of = ? WHERE id = ?",
            (new_subject, new_score, new_out_of, score_id),
        )

    return get(score_id)


def delete(score_id):
    """Delete a score. Returns the deleted record."""
    score = get(score_id)
    if not score:
        raise ValueError(f"Unknown score {score_id}")

    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM scores WHERE id = ?", (score_id,))

    return score