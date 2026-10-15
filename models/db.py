"""
Database connection and schema initialization.

Uses Python's built-in sqlite3. No ORM.

The schema is created on first run if the database file doesn't exist.
Future schema changes go in the migrations list at the bottom of this file.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DB_PATH


# --- Schema ---

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class TEXT NOT NULL,
    guardian_phone TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class TEXT NOT NULL,
    term TEXT NOT NULL,
    amount REAL NOT NULL,
    UNIQUE(class, term)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    term TEXT NOT NULL,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    term TEXT NOT NULL,
    subject TEXT NOT NULL,
    score REAL NOT NULL,
    out_of REAL NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id);
CREATE INDEX IF NOT EXISTS idx_payments_term ON payments(term);
CREATE INDEX IF NOT EXISTS idx_scores_student ON scores(student_id);
CREATE INDEX IF NOT EXISTS idx_scores_term ON scores(term);
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class);
"""


# --- Connection ---

def get_connection():
    """
    Open a connection to the database.
    Enables foreign key enforcement (SQLite disables it by default).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_cursor(commit=False):
    """
    Context manager for safe database access.

    Usage:
        with get_cursor(commit=True) as cur:
            cur.execute("INSERT INTO students VALUES (...)")
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Initialization ---

def init_db():
    """Create tables and indexes if they don't exist."""
    with get_cursor(commit=True) as cur:
        cur.executescript(SCHEMA)


def table_names():
    """Return the list of tables in the database. For tests and debugging."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
        return [row["name"] for row in cur.fetchall()]


def drop_all():
    """
    Drop all tables. DANGEROUS — used in tests only.
    """
    with get_cursor(commit=True) as cur:
        cur.executescript("""
            DROP TABLE IF EXISTS scores;
            DROP TABLE IF EXISTS payments;
            DROP TABLE IF EXISTS fees;
            DROP TABLE IF EXISTS students;
        """)


# --- Entry point ---

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH}")
    print(f"Tables: {', '.join(table_names())}")