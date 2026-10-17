"""
Migrate data from v1 JSON files to v2 SQLite database.

Usage:
    python -m scripts.migrate_from_json --source "C:\path\to\v1\data"
"""
import argparse
import json
import sys
from pathlib import Path

# Add the repo root to sys.path so we can import our models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import db, students, payments, scores, fees


def load_json(folder, filename):
    """Load a JSON file from the source folder. Returns [] if missing."""
    path = folder / filename
    if not path.exists():
        print(f"  ⚠ {filename} not found. Skipping.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate(source_dir):
    source = Path(source_dir)
    if not source.exists() or not source.is_dir():
        print(f"Error: Source directory '{source}' not found.")
        sys.exit(1)

    print(f"Starting migration from: {source}")
    print(f"Target database: {db.DB_PATH}")
    
    # Wipe existing data to start fresh (Careful! This deletes current v2 data)
    print("\nResetting v2 database...")
    db.drop_all()
    db.init_db()

    # --- 1. Migrate Fees ---
    fees_data = load_json(source, "fees.json")
    for f in fees_data:
        fees.set_fee(f["class"], f["term"], f["amount"])
    print(f"✅ Migrated {len(fees_data)} fee records")

    # --- 2. Migrate Students ---
    # We use a dictionary to map old IDs to new IDs, just in case.
    # In v2 we use the exact same string ID, so we just keep a set.
    students_data = load_json(source, "students.json")
    migrated_students = set()
    
    for s in students_data:
        try:
            students.create(
                student_id=s["id"],
                name=s["name"],
                student_class=s["class"],
                guardian_phone=s.get("guardian_phone", "")
            )
            migrated_students.add(s["id"])
        except ValueError as e:
            print(f"  ⚠ Skipping student {s['id']}: {e}")
            
    print(f"✅ Migrated {len(migrated_students)} students")

    # --- 3. Migrate Payments ---
    payments_data = load_json(source, "payments.json")
    migrated_payments = 0
    
    for p in payments_data:
        # Only migrate payments for students who successfully made it in
        if p["student_id"] in migrated_students:
            try:
                payments.create(
                    student_id=p["student_id"],
                    term=p["term"],
                    amount=p["amount"],
                    method=p.get("method", "cash"),
                    payment_date=p.get("date")
                )
                migrated_payments += 1
            except Exception as e:
                print(f"  ⚠ Skipping payment for {p['student_id']}: {e}")
                
    print(f"✅ Migrated {migrated_payments} payments")

    # --- 4. Migrate Scores ---
    scores_data = load_json(source, "scores.json")
    migrated_scores = 0
    
    for s in scores_data:
        if s["student_id"] in migrated_students:
            try:
                scores.create(
                    student_id=s["student_id"],
                    term=s["term"],
                    subject=s["subject"],
                    score=s["score"],
                    out_of=s.get("out_of", 100)
                )
                migrated_scores += 1
            except Exception as e:
                print(f"  ⚠ Skipping score for {s['student_id']}: {e}")
                
    print(f"✅ Migrated {migrated_scores} scores")

    print("\nMigration complete.")
    print(f"Total students: {students.count()}")
    print(f"Total payments: {payments.total_for_term('2026-T1')} (in 2026-T1)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate v1 JSON to v2 SQLite")
    parser.add_argument(
        "--source", 
        required=True, 
        help="Path to the v1 data folder containing JSON files"
    )
    args = parser.parse_args()
    
    migrate(args.source)