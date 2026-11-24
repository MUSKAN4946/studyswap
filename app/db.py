import sqlite3
from pathlib import Path

# Project ka root folder (studyswap/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Database file yahan banegi: studyswap/studyswap.db
DB_PATH = BASE_DIR / "studyswap.db"

# Schema file ka path: studyswap/app/schema.sql
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_conn() -> sqlite3.Connection:
    """Database se naya connection kholta hai."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    # Rows ko dictionary jaisa use kar sakein (row["title"])
    conn.row_factory = sqlite3.Row
    # Foreign key check ON: jo session exist nahi karta uski booking reject hogi
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """schema.sql padh kar tables, index aur trigger bana deta hai."""
    conn = get_conn()
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()