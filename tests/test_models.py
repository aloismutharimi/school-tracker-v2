"""
Tests for the model layer.
Verifies CRUD for each entity works and that cross-table logic holds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from models import db, students, payments, scores, fees


@pytest.fixture(autouse=True)
def fresh_db():
    """Wipe and recreate the schema before every test."""
    db.drop_all()
    db.init_db()
    yield


# ---------- Students ----------

def test_create_and_get_student():
    s = students.create("STU001", "Wanjiku Kamau", "Grade 2", "+254700000001")
    assert s["id"] == "STU001"
    assert s["name"] == "Wanjiku Kamau"
    assert s["class"] == "Grade 2"

    fetched = students.get("STU001")
    assert fetched["name"] == "Wanjiku Kamau"


def test_duplicate_student_rejected():
    students.create("STU001", "Wanjiku Kamau", "Grade 2")
    with pytest.raises(ValueError):
        students.create("STU001", "Someone Else", "Grade 3")


def test_list_students_by_class():
    students.create("STU001", "Alice", "Grade 1")
    students.create("STU002", "Brian", "Grade 2")
    students.create("STU003", "Carol", "Grade 1")

    grade_1 = students.list_by_class("Grade 1")
    assert len(grade_1) == 2
    assert {s["name"] for s in grade_1} == {"Alice", "Carol"}


def test_update_student():
    students.create("STU001", "Alice", "Grade 1")
    updated = students.update("STU001", name="Alice Wanjiru", guardian_phone="+254711111111")
    assert updated["name"] == "Alice Wanjiru"
    assert updated["guardian_phone"] == "+254711111111"
    assert updated["class"] == "Grade 1"  # unchanged


def test_delete_student():
    students.create("STU001", "Alice", "Grade 1")
    deleted = students.delete("STU001")
    assert deleted["name"] == "Alice"
    assert students.get("STU001") is None


def test_delete_student_cascades_to_payments_and_scores():
    students.create("STU001", "Alice", "Grade 1")
    payments.create("STU001", "2026-T1", 5000)
    scores.create("STU001", "2026-T1", "Mathematics", 85)

    assert len(payments.list_by_student("STU001")) == 1
    assert len(scores.list_by_student("STU001")) == 1

    students.delete("STU001")

    assert len(payments.list_by_student("STU001")) == 0
    assert len(scores.list_by_student("STU001")) == 0


# ---------- Fees ----------

def test_set_and_get_fee():
    fees.set_fee("Grade 2", "2026-T1", 7000)
    fee = fees.get("Grade 2", "2026-T1")
    assert fee["amount"] == 7000
    assert fees.amount("Grade 2", "2026-T1") == 7000


def test_set_fee_upserts():
    fees.set_fee("Grade 2", "2026-T1", 7000)
    fees.set_fee("Grade 2", "2026-T1", 7500)  # same class+term, new amount
    assert fees.amount("Grade 2", "2026-T1") == 7500


def test_missing_fee_returns_zero():
    assert fees.amount("Grade 99", "2026-T1") == 0.0


# ---------- Payments ----------

def test_create_payment():
    students.create("STU001", "Alice", "Grade 1")
    p = payments.create("STU001", "2026-T1", 5000, "mpesa", "2026-01-15")
    assert p["amount"] == 5000
    assert p["method"] == "mpesa"
    assert p["date"] == "2026-01-15"


def test_payment_total_for_student():
    students.create("STU001", "Alice", "Grade 1")
    payments.create("STU001", "2026-T1", 5000)
    payments.create("STU001", "2026-T1", 2000)
    payments.create("STU001", "2026-T2", 9999)  # different term

    assert payments.total_for_student("STU001", "2026-T1") == 7000
    assert payments.total_for_student("STU001", "2026-T2") == 9999
    assert payments.total_for_student("STU001", "2026-T3") == 0.0


def test_update_and_delete_payment():
    students.create("STU001", "Alice", "Grade 1")
    p = payments.create("STU001", "2026-T1", 5000)

    updated = payments.update(p["id"], amount=7500)
    assert updated["amount"] == 7500

    deleted = payments.delete(p["id"])
    assert deleted["amount"] == 7500
    assert payments.get(p["id"]) is None


# ---------- Scores ----------

def test_create_and_average_score():
    students.create("STU001", "Alice", "Grade 1")
    scores.create("STU001", "2026-T1", "Mathematics", 80)
    scores.create("STU001", "2026-T1", "English", 90)

    avg = scores.average_for_student("STU001", "2026-T1")
    assert avg == 85.0


def test_scores_by_class():
    students.create("STU001", "Alice", "Grade 1")
    students.create("STU002", "Brian", "Grade 2")
    scores.create("STU001", "2026-T1", "Mathematics", 80)
    scores.create("STU002", "2026-T1", "Mathematics", 70)

    grade_1_scores = scores.list_by_class_and_term("Grade 1", "2026-T1")
    assert len(grade_1_scores) == 1
    assert grade_1_scores[0]["score"] == 80


def test_average_returns_none_with_no_scores():
    students.create("STU001", "Alice", "Grade 1")
    assert scores.average_for_student("STU001", "2026-T1") is None