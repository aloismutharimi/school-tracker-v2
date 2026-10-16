"""
Student records.

All functions return plain dicts or lists of dicts, not sqlite3.Row objects.
That keeps the rest of the app decoupled from the database library.
"""
from datetime import datetime

from models.db import get_cursor


def _row_to_dict(row):
    """Convert a sqlite3.Row into a plain dict."""
    return dict(row) if row else None


def create(student_id, name, student_class, guardian_phone=""):
    """Insert a new student. Raises ValueError if the ID exists."""
    existing = get(student_id)
    if existing:
        raise ValueError(f"Student {student_id} already exists")

    now = datetime.now().isoformat(timespec="seconds")

    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO students (id, name, class, guardian_phone, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (student_id, name, student_class, guardian_phone, now),
        )

    return get(student_id)


def get(student_id):
    """Return a student dict, or None if not found."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        return _row_to_dict(cur.fetchone())


def list_all():
    """Return all students, sorted by class then name."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM students ORDER BY class, name")
        return [dict(row) for row in cur.fetchall()]


def list_by_class(student_class):
    """Return all students in a given class."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM students WHERE class = ? ORDER BY name",
            (student_class,),
        )
        return [dict(row) for row in cur.fetchall()]


def update(student_id, name=None, student_class=None, guardian_phone=None):
    """Update a student's fields. Returns the updated record."""
    student = get(student_id)
    if not student:
        raise ValueError(f"Unknown student {student_id}")

    # Only update fields that were actually passed
    new_name = name if name is not None else student["name"]
    new_class = student_class if student_class is not None else student["class"]
    new_phone = (
        guardian_phone
        if guardian_phone is not None
        else student.get("guardian_phone", "")
    )

    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE students SET name = ?, class = ?, guardian_phone = ? "
            "WHERE id = ?",
            (new_name, new_class, new_phone, student_id),
        )

    return get(student_id)


def delete(student_id):
    """
    Delete a student. Payments and scores are removed automatically
    by the ON DELETE CASCADE rules.
    """
    student = get(student_id)
    if not student:
        raise ValueError(f"Unknown student {student_id}")

    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))

    return student


def count():
    """Return the total number of students."""
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM students")
        return cur.fetchone()["c"]


def known_classes():
    """Return a sorted list of class names in use."""
    with get_cursor() as cur:
        cur.execute("SELECT DISTINCT class FROM students ORDER BY class")
        return [row["class"] for row in cur.fetchall()]