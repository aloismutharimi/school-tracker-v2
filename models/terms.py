from models.db import get_cursor

def list_terms():
    """Return all terms, newest first."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM terms ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]

def get_active_term():
    """Return the currently active term ID. Defaults to the latest if none active."""
    with get_cursor() as cur:
        cur.execute("SELECT id FROM terms WHERE is_active = 1 LIMIT 1")
        row = cur.fetchone()
        if row:
            return row["id"]
        
        # If none active, get the most recent one
        cur.execute("SELECT id FROM terms ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return row["id"]
            
        return "2026-T1" # Fallback

def set_active_term(term_id):
    """Set a term as active and deactivate the rest."""
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE terms SET is_active = 0")
        cur.execute(
            "INSERT INTO terms (id, is_active) VALUES (?, 1) "
            "ON CONFLICT(id) DO UPDATE SET is_active = 1",
            (term_id,)
        )

def create_term(term_id):
    """Add a new term to the database."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO terms (id, is_active) VALUES (?, 0) "
            "ON CONFLICT(id) DO NOTHING",
            (term_id,)
        )