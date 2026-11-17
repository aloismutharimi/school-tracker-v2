from models.db import init_db
from models.students import create, count
from models.terms import create_term, set_active_term
from models.fees import set_fee
from models import payments, scores

def seed_if_empty():
    """If the database is empty, populate it with demo data."""
    init_db()
    
    # If we already have students, do nothing (prevents duplicating data on restarts)
    if count() > 0:
        return
        
    print("Empty database detected. Seeding demo data...")
    
    # 1. Set up Term
    create_term("2026-T1")
    set_active_term("2026-T1")
    
    # 2. Add Fee Schedule
    set_fee("Grade 2", "2026-T1", 7000)
    
    # 3. Add 5 Students
    create("STU001", "Wanjiku Kamau", "Grade 2", "+254700000001")
    create("STU002", "Brian Otieno", "Grade 2", "+254700000002")
    create("STU003", "Amina Hassan", "Grade 2", "+254700000003")
    create("STU004", "Kipchoge Rotich", "Grade 2", "+254700000004")
    create("STU005", "Njeri Mwangi", "Grade 2", "+254700000005")
    
    # 4. Add Payments
    payments.create("STU001", "2026-T1", 7000, "mpesa") # Fully paid
    payments.create("STU002", "2026-T1", 3000, "cash")  # Partial
    payments.create("STU003", "2026-T1", 7000, "bank")  # Fully paid
    # STU004 and STU005 have 0 payments (Arrears)
    
    # 5. Add Scores
    scores.create("STU001", "2026-T1", "Mathematics", 85)
    scores.create("STU001", "2026-T1", "English", 78)
    
    scores.create("STU002", "2026-T1", "Mathematics", 65)
    scores.create("STU002", "2026-T1", "English", 72)
    
    scores.create("STU003", "2026-T1", "Mathematics", 92)
    scores.create("STU003", "2026-T1", "English", 88)
    
    scores.create("STU004", "2026-T1", "Mathematics", 55)
    scores.create("STU004", "2026-T1", "English", 60)
    
    scores.create("STU005", "2026-T1", "Mathematics", 76)
    scores.create("STU005", "2026-T1", "English", 81)
    
    print("✅ Demo data seeded successfully.")