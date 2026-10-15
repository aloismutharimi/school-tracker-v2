"""
Tests for the database foundation.
Verifies that the schema is created, tables exist, and basic operations work.
"""
import sys
from pathlib import Path

# Make the repo root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from models import db


def setup_module(module):
    """Fresh database before these tests run."""
    db.drop_all()
    db.init_db()


def test_tables_exist():
    """All four tables should exist after init."""
    tables = db.table_names()
    assert "students" in tables
    assert "payments" in tables
    assert "scores" in tables
    assert "fees" in tables


def test_insert_and_read_student():
    """Can insert a student and read it back."""
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO students (id, name, class, guardian_phone, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("STU001", "Wanjiku Kamau", "Grade 2", "+254700000001", "2026-01-15"),
        )

    with db.get_cursor() as cur:
        cur.execute("SELECT * FROM students WHERE id = ?", ("STU001",))
        row = cur.fetchone()

    assert row is not None
    assert row["name"] == "Wanjiku Kamau"
    assert row["class"] == "Grade 2"


def test_foreign_key_cascade():
    """
    Deleting a student should delete their payments and scores.
    This proves foreign key enforcement is on.
    """
    # Insert a student with a payment and a score
    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO students (id, name, class, created_at) "
            "VALUES (?, ?, ?, ?)",
            ("STU002", "Brian Otieno", "Grade 2", "2026-01-15"),
        )
        cur.execute(
            "INSERT INTO payments (student_id, term, amount, method, date, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("STU002", "2026-T1", 5000, "mpesa", "2026-01-20", "2026-01-20"),
        )
        cur.execute(
            "INSERT INTO scores (student_id, term, subject, score, out_of, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("STU002", "2026-T1", "Mathematics", 85, 100, "2026-02-01"),
        )

    # Confirm both child records exist
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM payments WHERE student_id = ?", ("STU002",))
        assert cur.fetchone()["c"] == 1
        cur.execute("SELECT COUNT(*) AS c FROM scores WHERE student_id = ?", ("STU002",))
        assert cur.fetchone()["c"] == 1

    # Delete the student
    with db.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM students WHERE id = ?", ("STU002",))

    # Child records should be gone
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM payments WHERE student_id = ?", ("STU002",))
        assert cur.fetchone()["c"] == 0
        cur.execute("SELECT COUNT(*) AS c FROM scores WHERE student_id = ?", ("STU002",))
        assert cur.fetchone()["c"] == 0


def test_unique_fee_constraint():
    """
    The fees table has UNIQUE(class, term).
    Trying to insert the same pair twice should fail.
    """
    import sqlite3

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO fees (class, term, amount) VALUES (?, ?, ?)",
            ("Grade 3", "2026-T1", 9000),
        )

    with pytest.raises(sqlite3.IntegrityError):
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO fees (class, term, amount) VALUES (?, ?, ?)",
                ("Grade 3", "2026-T1", 9000),
            )