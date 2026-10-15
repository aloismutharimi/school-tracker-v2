"""
Configuration for School Tracker v2.

Handles environment detection, data paths, and database location.
The same code runs both locally and on a server — only the
data location changes.
"""
import os
from pathlib import Path


# --- Environment ---

# "development" or "production"
ENV = os.environ.get("SCHOOL_TRACKER_ENV", "development")
IS_PRODUCTION = ENV == "production"


# --- Data directory ---

# Priority:
# 1. SCHOOL_TRACKER_DATA environment variable (explicit override)
# 2. ./data relative to the current working directory (default)
_env_data = os.environ.get("SCHOOL_TRACKER_DATA")
if _env_data:
    DATA_DIR = Path(_env_data).resolve()
else:
    DATA_DIR = (Path.cwd() / "data").resolve()

DATA_DIR.mkdir(parents=True, exist_ok=True)


# --- Database ---

DB_PATH = DATA_DIR / "school_tracker.db"


# --- Flask ---

# In production, SECRET_KEY must come from the environment.
# In development, a default is fine.
SECRET_KEY = os.environ.get(
    "SCHOOL_TRACKER_SECRET",
    "dev-secret-change-me-in-production",
)

if IS_PRODUCTION and SECRET_KEY == "dev-secret-change-me-in-production":
    raise RuntimeError(
        "SECRET_KEY must be set via SCHOOL_TRACKER_SECRET in production."
    )


# --- Application ---

APP_NAME = "School Tracker"
DEFAULT_TERM = "2026-T1"


# --- Convenience for debugging ---

def describe():
    """Return a human-readable summary of the current config."""
    return (
        f"Environment: {ENV}\n"
        f"Data directory: {DATA_DIR}\n"
        f"Database: {DB_PATH}\n"
        f"Default term: {DEFAULT_TERM}"
    )


if __name__ == "__main__":
    print(describe())